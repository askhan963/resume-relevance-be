"""
ATS Score Endpoints

POST /api/v1/ats/score    — Get a standalone ATS score for a resume vs JD
GET  /api/v1/ats/tips     — Get general ATS optimization tips (static)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...crud.crud_job_description import crud_job_description
from ...crud.crud_resume import crud_resume
from ...schemas.analysis import ATSScoreRequest, ATSScoreResponse
from ...services.chains.ats_chain import run_ats_chain
from ..dependencies import get_current_user

router = APIRouter(prefix="/ats", tags=["ATS Scoring"])


@router.post("/score", response_model=ATSScoreResponse)
async def get_ats_score(
    request: ATSScoreRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ATSScoreResponse:
    """
    Get a standalone ATS compatibility score for a resume against a job description.

    This is a lighter call than the full analysis — it only runs the ATS chain.

    Returns:
    - **ats_score**: ATS compatibility score (0–100)
    - **missing_keywords**: Important keywords the ATS might miss
    - **recommendations**: Specific ATS improvement suggestions
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
        raise HTTPException(status_code=422, detail="Resume has no extracted text.")

    try:
        result = await run_ats_chain(
            resume_text=resume["extracted_text"],
            jd_text=jd["raw_text"],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return ATSScoreResponse(
        ats_score=float(result["ats_score"]),
        missing_keywords=result.get("missing_keywords", []),
        recommendations=result.get("recommendations", []),
    )


@router.get("/tips")
async def get_ats_tips() -> dict:
    """
    Get a list of general ATS optimization tips.

    These are static best-practice tips, not personalized to a specific resume.
    """
    tips = [
        "Use standard section headers: 'Work Experience', 'Education', 'Skills', 'Summary'.",
        "Avoid tables, columns, headers/footers, and text boxes — ATS parsers often skip them.",
        "Use common file formats: PDF or DOCX (avoid Google Docs exports unless converted).",
        "Include keywords from the job description verbatim (not just synonyms).",
        "Quantify achievements where possible: '↑ Sales by 30%' over 'Improved sales'.",
        "Use a clean, single-column layout without fancy graphics or charts.",
        "Include a dedicated 'Skills' section with relevant technical and soft skills.",
        "Tailor your resume for each application — generic resumes score poorly.",
        "Avoid using images, logos, or scanned documents — ATS cannot read image text.",
        "Keep your resume to 1–2 pages with consistent formatting.",
    ]
    return {"tips": tips, "count": len(tips)}
