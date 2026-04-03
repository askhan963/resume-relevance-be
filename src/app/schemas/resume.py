from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class ResumeBase(BaseModel):
    original_filename: Annotated[str, Field(examples=["my_resume.pdf"])]
    file_type: Annotated[str, Field(examples=["pdf"])]


class ResumeRead(ResumeBase):
    """Response schema for a single resume."""

    id: int
    user_id: int
    file_url: str
    extracted_text: str | None = None
    latest_ats_score: float | None = None
    latest_relevance_score: float | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Response returned after a successful resume upload."""

    id: int
    message: str = "Resume uploaded and text extracted successfully."
    original_filename: str
    file_url: str
    file_type: str
    extracted_text_preview: str | None = None  # First 300 chars of extracted text

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    """Paginated list of resumes."""

    total: int
    data: list[ResumeRead]


class ResumeCreateInternal(ResumeBase):
    """Internal schema used when saving a resume to DB."""

    user_id: int
    file_url: str
    extracted_text: str | None = None
