from typing import Annotated

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request body to trigger a full resume analysis."""

    resume_id: Annotated[int, Field(description="ID of the uploaded resume to analyze.")]
    job_description_id: Annotated[int, Field(description="ID of the job description to match against.")]


class AnalysisResult(BaseModel):
    """
    Raw analysis result returned by the AI chains.
    This is used internally and also surfaced in the ReportRead schema.
    """

    relevance_score: float = Field(ge=0, le=100, description="How well the resume matches the JD (0–100).")
    ats_score: float = Field(ge=0, le=100, description="ATS-friendliness score (0–100).")
    matched_keywords: list[str] = Field(default_factory=list, description="Keywords found in both resume and JD.")
    missing_keywords: list[str] = Field(default_factory=list, description="Important JD keywords absent from resume.")
    recommendations: list[str] = Field(default_factory=list, description="Actionable suggestions to improve the resume.")


class ATSScoreRequest(BaseModel):
    """Request body for a standalone ATS score check."""

    resume_id: int
    job_description_id: int


class ATSScoreResponse(BaseModel):
    """Response for ATS scoring."""

    ats_score: float
    missing_keywords: list[str]
    recommendations: list[str]


class RewriteRequest(BaseModel):
    """Request body for AI resume rewrite."""

    resume_id: int
    job_description_id: int


class RewriteResponse(BaseModel):
    """Response after AI rewrites the resume."""

    report_id: int
    optimized_resume_text: str
    message: str = "Resume rewritten successfully. Download link generated."
    optimized_file_url: str | None = None
