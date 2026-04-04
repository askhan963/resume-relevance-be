"""
Rewrite Endpoints

POST /api/v1/rewrite/    — Generate an AI-optimized rewrite of a resume
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
from ...schemas.analysis import RewriteRequest, RewriteResponse
from ...schemas.report import ReportUpdateInternal
from ...services.analysis_service import rewrite_resume
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rewrite", tags=["Resume Rewrite"])


@router.post("/", response_model=RewriteResponse)
async def rewrite_resume_endpoint(
    request: RewriteRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> RewriteResponse:
    """
    Generate an AI-optimized rewrite of a resume tailored to a specific job description.

    If an existing analysis report exists for this resume + JD pair, the rewrite will
    incorporate the identified missing keywords and recommendations for best results.

    > ⚠️ This endpoint calls an external LLM API. Typical response time: 10–30 seconds.

    Returns the rewritten resume text. The result is also saved to the most recent
    matching report record for future retrieval.
    """
    # Validate ownership
    resume = await crud_resume.get(db, id=request.resume_id, is_deleted=False)
    if not resume:
        raise NotFoundException("Resume not found.")
    if resume["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this resume.")

    jd = await crud_job_description.get(db, id=request.job_description_id, is_deleted=False)
    if not jd:
        raise NotFoundException("Job description not found.")
    if jd["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this job description.")

    if not resume.get("extracted_text"):
        raise HTTPException(status_code=422, detail="Resume has no extracted text. Please re-upload.")

    # Find existing report for this pair (to use keywords/recommendations)
    existing_reports = await crud_report.get_multi(
        db,
        user_id=current_user["id"],
        resume_id=request.resume_id,
        job_description_id=request.job_description_id,
        limit=1,
    )
    existing_report = existing_reports["data"][0] if existing_reports["data"] else None

    missing_keywords = existing_report.get("missing_keywords") if existing_report else None
    recommendations = existing_report.get("recommendations") if existing_report else None

    # Run the rewrite chain
    try:
        optimized_text = await rewrite_resume(
            resume_text=resume["extracted_text"],
            jd_text=jd["raw_text"],
            missing_keywords=missing_keywords,
            recommendations=recommendations,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Save optimized text to the existing report (or note it in the response)
    report_id = existing_report["id"] if existing_report else None
    if report_id:
        await crud_report.update(
            db,
            object=ReportUpdateInternal(
                optimized_resume_text=optimized_text,
                updated_at=datetime.now(UTC),
            ),
            id=report_id,
        )

    return RewriteResponse(
        report_id=report_id or 0,
        optimized_resume_text=optimized_text,
        message="Resume rewritten successfully. Use /api/v1/files/download/{report_id}/resume to get the file.",
    )
