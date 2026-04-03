"""
Resume Endpoints

POST   /api/v1/resumes/upload    — Upload PDF/DOCX resume
GET    /api/v1/resumes/          — List authenticated user's resumes
GET    /api/v1/resumes/{id}      — Get a single resume by ID
DELETE /api/v1/resumes/{id}      — Soft-delete a resume
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.logger import logging
from ...crud.crud_resume import crud_resume
from ...schemas.resume import ResumeCreateInternal, ResumeListResponse, ResumeRead, ResumeUploadResponse
from ...services import file_service, storage_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    file: UploadFile,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ResumeUploadResponse:
    """
    Upload a resume (PDF or DOCX).

    - Validates file type and size
    - Extracts text content from the file
    - Uploads the original file to Supabase Storage
    - Saves file metadata and extracted text to the database

    Returns the resume record with a preview of extracted text.
    """
    file_bytes = await file.read()

    # Validate file
    try:
        file_service.validate_file(
            filename=file.filename or "resume",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
            max_size_mb=settings.MAX_FILE_SIZE_MB,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Extract text
    try:
        extracted_text = file_service.extract_text(
            filename=file.filename or "resume",
            file_bytes=file_bytes,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Upload to Supabase Storage
    try:
        file_url = await storage_service.upload_file(
            file_bytes=file_bytes,
            original_filename=file.filename or "resume",
            user_id=current_user["id"],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Determine file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()

    # Save to DB
    resume_data = ResumeCreateInternal(
        user_id=current_user["id"],
        original_filename=file.filename or "resume",
        file_url=file_url,
        file_type=ext,
        extracted_text=extracted_text,
    )
    created = await crud_resume.create(db, object=resume_data)

    preview = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text

    return ResumeUploadResponse(
        id=created["id"],
        original_filename=file.filename or "resume",
        file_url=file_url,
        file_type=ext,
        extracted_text_preview=preview,
    )


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    page_size: int = 10,
) -> ResumeListResponse:
    """
    List all resumes for the authenticated user (paginated).
    """
    offset = (page - 1) * page_size
    result = await crud_resume.get_multi(
        db,
        user_id=current_user["id"],
        is_deleted=False,
        offset=offset,
        limit=page_size,
    )
    return ResumeListResponse(total=result["total_count"], data=result["data"])


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ResumeRead:
    """
    Get a single resume by its ID.

    Only the owner can access their resumes.
    """
    resume = await crud_resume.get(db, id=resume_id, is_deleted=False)
    if not resume:
        raise NotFoundException("Resume not found.")
    if resume["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this resume.")
    return resume


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> None:
    """
    Soft-delete a resume by ID.

    The file in Supabase Storage is also deleted.
    """
    resume = await crud_resume.get(db, id=resume_id, is_deleted=False)
    if not resume:
        raise NotFoundException("Resume not found.")
    if resume["user_id"] != current_user["id"]:
        raise ForbiddenException("You do not have access to this resume.")

    # Delete from Supabase Storage
    try:
        await storage_service.delete_file(resume["file_url"])
    except RuntimeError as e:
        logger.warning(f"Could not delete file from storage during resume deletion: {e}")

    # Soft-delete in DB
    await crud_resume.update(db, object={"is_deleted": True}, id=resume_id)
