from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReportRead(BaseModel):
    """Full report response schema."""

    id: int
    user_id: int
    resume_id: int
    job_description_id: int
    status: str

    relevance_score: float | None = None
    ats_score: float | None = None
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None = None
    recommendations: list[str] | None = None
    optimized_resume_text: str | None = None
    optimized_file_url: str | None = None
    error_message: str | None = None

    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReportSummary(BaseModel):
    """Lightweight report summary for history listing."""

    id: int
    resume_id: int
    job_description_id: int
    status: str
    relevance_score: float | None = None
    ats_score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportHistoryResponse(BaseModel):
    """Paginated report history."""

    total: int
    data: list[ReportSummary]


class ReportCreateInternal(BaseModel):
    """Internal schema for creating a new report record."""

    user_id: int
    resume_id: int
    job_description_id: int
    status: str = "pending"


class ReportUpdateInternal(BaseModel):
    """Internal schema for updating a report after analysis completes."""

    status: str | None = None
    relevance_score: float | None = None
    ats_score: float | None = None
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None = None
    recommendations: list[str] | None = None
    optimized_resume_text: str | None = None
    optimized_file_url: str | None = None
    error_message: str | None = None
    updated_at: datetime | None = None
