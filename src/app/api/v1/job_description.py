"""
Job Description Endpoints

POST   /api/v1/job-descriptions/           — Create a JD (paste text)
POST   /api/v1/job-descriptions/upload     — Upload JD as PDF/DOCX
GET    /api/v1/job-descriptions/           — List authenticated user's JDs
GET    /api/v1/job-descriptions/{id}       — Get a single JD by ID
DELETE /api/v1/job-descriptions/{id}       — Delete a JD
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...crud.crud_job_description import crud_job_description
from ...schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionCreateInternal,
    JobDescriptionListResponse,
    JobDescriptionRead,
)
from ...services import file_service, storage_service
from ..dependencies import get_current_user

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@router.post("/", response_model=JobDescriptionRead, status_code=201)
async def create_job_description(
    jd_in: JobDescriptionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> JobDescriptionRead:
    """
    Create a new job description by pasting the text directly.

    Provide an optional title and company name for organization.
    """
    internal_data = JobDescriptionCreateInternal(
        user_id=current_user["id"],
        title=jd_in.title,
        company=jd_in.company,
        raw_text=jd_in.raw_text,
        source="pasted",
    )
    created = await crud_job_description.create(db, object=internal_data)
    return created


@router.post("/upload", response_model=JobDescriptionRead, status_code=201)
async def upload_job_description(
    file: UploadFile,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    title: str | None = None,
    company: str | None = None,
) -> JobDescriptionRead:
    """
    Upload a job description as a PDF or DOCX file.

    Text is extracted from the file and stored in the database.
    The original file is also saved to Supabase Storage.
    """
    file_bytes = await file.read()

    # Validate
    try:
        file_service.validate_file(
            filename=file.filename or "jd",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
            max_size_mb=settings.MAX_FILE_SIZE_MB,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Extract text
    try:
        raw_text = file_service.extract_text(filename=file.filename or "jd", file_bytes=file_bytes)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Upload to storage
    try:
        file_url = await storage_service.upload_file(
            file_bytes=file_bytes,
            original_filename=file.filename or "jd",
            user_id=current_user["id"],
            bucket=settings.SUPABASE_STORAGE_BUCKET,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    internal_data = JobDescriptionCreateInternal(
        user_id=current_user["id"],
        title=title,
        company=company,
        raw_text=raw_text,
        source="uploaded",
        file_url=file_url,
    )
    created = await crud_job_description.create(db, object=internal_data)
    return created


@router.get("/", response_model=JobDescriptionListResponse)
async def list_job_descriptions(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    page_size: int = 10,
) -> JobDescriptionListResponse:
    """
    List all job descriptions for the authenticated user (paginated).
    """
    offset = (page - 1) * page_size
    result = await crud_job_description.get_multi(
        db,
        user_id=current_user["id"],
        is_deleted=False,
        offset=offset,
        limit=page_size,
    )
    return JobDescriptionListResponse(total=result["total_count"], data=result["data"])


@router.get("/{jd_id}", response_model=JobDescriptionRead)
async def get_job_description(
    jd_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> JobDescriptionRead:
    """
    Get a single job description by ID.
    """
    jd = await crud_job_description.get(db, id=jd_id, is_deleted=False)
    if not jd:
        raise NotFoundException("Job description not found.")
    if jd["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this job description.")
    return jd


@router.delete("/{jd_id}", status_code=204)
async def delete_job_description(
    jd_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    """
    Delete a job description by ID.
    """
    jd = await crud_job_description.get(db, id=jd_id, is_deleted=False)
    if not jd:
        raise NotFoundException("Job description not found.")
    if jd["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this job description.")

    await crud_job_description.update(db, object={"is_deleted": True}, id=jd_id)
