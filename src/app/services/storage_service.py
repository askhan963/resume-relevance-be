"""
Supabase Storage service for uploading, downloading, and deleting files.

Uses the official supabase-py client with service role key for server-side operations.
"""

import logging
import uuid
from io import BytesIO

logger = logging.getLogger(__name__)


def _get_client():
    """Lazily initialize the Supabase client to avoid import errors if not configured."""
    try:
        from supabase import create_client

        from ..core.config import settings

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file."
            )

        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except ImportError:
        raise RuntimeError("supabase-py is not installed. Run: pip install supabase")


async def upload_file(
    file_bytes: bytes,
    original_filename: str,
    user_id: int,
    bucket: str | None = None,
) -> str:
    """
    Upload a file to Supabase Storage and return its public URL.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content.
    original_filename : str
        Original filename (used to derive extension and MIME type).
    user_id : int
        User ID — used to namespace files by user (e.g., user_42/uuid.pdf).
    bucket : str | None
        Storage bucket name. Defaults to SUPABASE_STORAGE_BUCKET from settings.

    Returns
    -------
    str
        Public URL of the uploaded file.

    Raises
    ------
    RuntimeError
        If the upload fails.
    """
    from ..core.config import settings

    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"

    # Determine MIME type
    mime_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    content_type = mime_map.get(ext, "application/octet-stream")

    # Build a unique storage path: {user_id}/{uuid}.{ext}
    storage_path = f"{user_id}/{uuid.uuid4()}.{ext}"

    try:
        client = _get_client()
        response = client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )

        # Build the public URL
        public_url = client.storage.from_(bucket).get_public_url(storage_path)
        logger.info(f"Uploaded file to Supabase Storage: {storage_path}")
        return public_url

    except Exception as e:
        logger.error(f"Supabase upload failed for path '{storage_path}': {e}")
        raise RuntimeError(f"File upload failed: {e}") from e


async def download_file(file_url: str, bucket: str | None = None) -> bytes:
    """
    Download a file from Supabase Storage by its public URL.

    Parameters
    ----------
    file_url : str
        The public URL of the file in Supabase Storage.
    bucket : str | None
        Storage bucket name. Defaults to SUPABASE_STORAGE_BUCKET from settings.

    Returns
    -------
    bytes
        Raw file bytes.
    """
    from ..core.config import settings

    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    # Extract the storage path from the URL
    # URL format: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
    try:
        storage_path = file_url.split(f"/object/public/{bucket}/")[-1]
        client = _get_client()
        file_bytes: bytes = client.storage.from_(bucket).download(storage_path)
        logger.info(f"Downloaded file from Supabase Storage: {storage_path}")
        return file_bytes
    except Exception as e:
        logger.error(f"Supabase download failed: {e}")
        raise RuntimeError(f"File download failed: {e}") from e


async def delete_file(file_url: str, bucket: str | None = None) -> None:
    """
    Delete a file from Supabase Storage by its public URL.

    Parameters
    ----------
    file_url : str
        The public URL of the file to delete.
    bucket : str | None
        Storage bucket name. Defaults to SUPABASE_STORAGE_BUCKET from settings.
    """
    from ..core.config import settings

    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    try:
        storage_path = file_url.split(f"/object/public/{bucket}/")[-1]
        client = _get_client()
        client.storage.from_(bucket).remove([storage_path])
        logger.info(f"Deleted file from Supabase Storage: {storage_path}")
    except Exception as e:
        logger.error(f"Supabase delete failed: {e}")
        raise RuntimeError(f"File deletion failed: {e}") from e
