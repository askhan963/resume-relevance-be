"""
Analysis Endpoints

POST /api/v1/analysis/           — Trigger full analysis (resume + JD)
GET  /api/v1/analysis/{id}       — Get a specific analysis report
GET  /api/v1/analysis/history    — List user's analysis history
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.logger import logging
from ...crud.crud_job_description import crud_job_description
from ...crud.crud_report import crud_report
from ...crud.crud_resume import crud_resume
from ...schemas.analysis import AnalysisRequest
from ...schemas.report import ReportCreateInternal, ReportHistoryResponse, ReportRead, ReportUpdateInternal
from ...services.analysis_service import analyze_resume
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/", response_model=ReportRead, status_code=201)
async def trigger_analysis(
    request: AnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ReportRead:
    """
    Trigger a full AI analysis of a resume against a job description.

    This runs two LangChain chains concurrently:
    - **Relevance Score Chain**: Scores how well the resume matches the JD (0–100)
    - **ATS Score Chain**: Scores ATS compatibility (0–100)

    Returns the full analysis report with scores, matched/missing keywords, and recommendations.

    > ⚠️ This endpoint calls an external LLM API (Groq/Gemini). Typical response time: 5–20 seconds.
    """
    # Validate resume ownership
    resume = await crud_resume.get(db, id=request.resume_id, is_deleted=False)
    if not resume:
        raise NotFoundException("Resume not found.")
    if resume["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this resume.")

    # Validate JD ownership
    jd = await crud_job_description.get(db, id=request.job_description_id, is_deleted=False)
    if not jd:
        raise NotFoundException("Job description not found.")
    if jd["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this job description.")

    # Check resume has extracted text
    if not resume.get("extracted_text"):
        raise HTTPException(status_code=422, detail="Resume has no extracted text. Please re-upload.")

    # Create a pending report record
    report_create = ReportCreateInternal(
        user_id=current_user["id"],
        resume_id=request.resume_id,
        job_description_id=request.job_description_id,
        status="processing",
    )
    report = await crud_report.create(db, object=report_create)
    report_id = report["id"]

    # Run analysis
    try:
        result = await analyze_resume(
            resume_text=resume["extracted_text"],
            jd_text=jd["raw_text"],
        )

        # Update report with results
        update_data = ReportUpdateInternal(
            status="completed",
            relevance_score=result.relevance_score,
            ats_score=result.ats_score,
            matched_keywords=result.matched_keywords,
            missing_keywords=result.missing_keywords,
            recommendations=result.recommendations,
            updated_at=datetime.now(UTC),
        )

    except Exception as e:
        logger.error(f"Analysis failed for report {report_id}: {e}")
        update_data = ReportUpdateInternal(
            status="failed",
            error_message=str(e),
            updated_at=datetime.now(UTC),
        )

    await crud_report.update(db, object=update_data, id=report_id)

    # Return the final report
    final_report = await crud_report.get(db, id=report_id)
    if not final_report:
        raise HTTPException(status_code=500, detail="Failed to retrieve completed report.")
    return final_report


@router.get("/history", response_model=ReportHistoryResponse)
async def get_analysis_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    page_size: int = 10,
) -> ReportHistoryResponse:
    """
    List the authenticated user's analysis history (paginated, newest first).
    """
    offset = (page - 1) * page_size
    result = await crud_report.get_multi(
        db,
        user_id=current_user["id"],
        offset=offset,
        limit=page_size,
    )
    return ReportHistoryResponse(total=result["total_count"], data=result["data"])


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ReportRead:
    """
    Get a specific analysis report by ID.
    """
    report = await crud_report.get(db, id=report_id)
    if not report:
        raise NotFoundException("Report not found.")
    if report["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this report.")
    return report
