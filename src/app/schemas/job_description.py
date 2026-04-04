from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class JobDescriptionBase(BaseModel):
    title: Annotated[str | None, Field(max_length=255, examples=["Senior Python Engineer"], default=None)]
    company: Annotated[str | None, Field(max_length=255, examples=["Acme Corp"], default=None)]
    raw_text: Annotated[str, Field(min_length=50, description="Full job description text.")]


class JobDescriptionCreate(JobDescriptionBase):
    """Schema for creating a JD via text paste."""

    source: Literal["pasted"] = "pasted"


class JobDescriptionCreateInternal(JobDescriptionBase):
    """Internal schema with user_id and source info."""

    user_id: int
    source: str = "pasted"
    file_url: str | None = None


class JobDescriptionRead(JobDescriptionBase):
    """Response schema for a job description."""

    id: int
    user_id: int
    source: str
    file_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobDescriptionListResponse(BaseModel):
    """Paginated list of job descriptions."""

    total: int
    data: list[JobDescriptionRead]
