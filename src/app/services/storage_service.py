"""
Storage service for uploading, downloading, and deleting files.
Supports both Supabase Storage and local file storage.
"""

import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_supabase_client():
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


def _get_local_storage_path():
    """Get the local storage path from settings."""
    from ..core.config import settings

    # Default to a storage directory in the project root
    storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', 'storage')
    # Ensure it's an absolute path
    if not os.path.isabs(storage_path):
        # Make it relative to the project root
        project_root = Path(__file__).parent.parent.parent.parent
        storage_path = project_root / storage_path

    # Ensure the directory exists
    os.makedirs(storage_path, exist_ok=True)
    return str(storage_path)


def _should_use_local_storage():
    """Check if we should use local storage instead of Supabase."""
    from ..core.config import settings
    return getattr(settings, 'USE_LOCAL_STORAGE', False)


def _get_content_type(filename: str) -> str:
    """Determine content type based on file extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    mime_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }
    return mime_map.get(ext, "application/octet-stream")


async def upload_file(
    file_bytes: bytes,
    original_filename: str,
    user_id: int,
    bucket: str | None = None,
) -> str:
    """
    Upload a file to storage (Supabase or local) and return its URL/path.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content.
    original_filename : str
        Original filename (used to derive extension and MIME type).
    user_id : int
        User ID — used to namespace files by user (e.g., user_42/uuid.pdf).
    bucket : str | None
        Storage bucket name (for Supabase) or subdirectory (for local).
        Defaults to SUPABASE_STORAGE_BUCKET for Supabase or "uploads" for local.

    Returns
    -------
    str
        Public URL (for Supabase) or relative path (for local storage).
    """
    # Check if we should use local storage
    if _should_use_local_storage():
        return await _upload_file_local(file_bytes, original_filename, user_id, bucket)
    else:
        return await _upload_file_supabase(file_bytes, original_filename, user_id, bucket)


async def _upload_file_supabase(
    file_bytes: bytes,
    original_filename: str,
    user_id: int,
    bucket: str | None = None,
) -> str:
    """Upload file to Supabase Storage."""
    from ..core.config import settings

    client = _get_supabase_client()
    bucket_name = bucket or settings.SUPABASE_STORAGE_BUCKET

    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    # User-namespaced path: e.g., user_42/uuid.pdf
    path = f"user_{user_id}/{unique_filename}"

    # Upload the file
    res = client.storage.from_(bucket_name).upload(
        path,
        file_bytes,
        {"content-type": _get_content_type(original_filename)},
    )

    # Handle potential upload errors
    if hasattr(res, "error") and res.error:
        raise RuntimeError(f"Failed to upload file: {res.error.message}")

    # Get public URL
    public_url = client.storage.from_(bucket_name).get_public_url(path)
    return public_url


async def _upload_file_local(
    file_bytes: bytes,
    original_filename: str,
    user_id: int,
    bucket: str | None = None,
) -> str:
    """Upload file to local storage."""
    # Get local storage base path
    base_path = _get_local_storage_path()

    # Determine storage directory (bucket for Supabase, subdirectory for local)
    storage_dir = bucket or "uploads"
    user_dir = f"user_{user_id}"

    # Create the full directory path
    save_dir = os.path.join(base_path, storage_dir, user_dir)
    os.makedirs(save_dir, exist_ok=True)

    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(save_dir, unique_filename)

    # Write the file
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Return a relative path that can be used to access the file
    # Format: /{storage_dir}/user_{user_id}/{unique_filename}
    relative_path = f"/{storage_dir}/{user_dir}/{unique_filename}"
    return relative_path


async def download_file(file_url: str, bucket: str | None = None) -> bytes:
    """
    Download a file from storage (Supabase or local) by its URL/path.

    Parameters
    ----------
    file_url : str
        The public URL (for Supabase) or relative path (for local) of the file.
    bucket : str | None
        Storage bucket name (for Supabase) or subdirectory (for local).
        Defaults to SUPABASE_STORAGE_BUCKET for Supabase or "uploads" for local.

    Returns
    -------
    bytes
        Raw file bytes.
    """
    # Check if we should use local storage
    if _should_use_local_storage():
        return await _download_file_local(file_url, bucket)
    else:
        return await _download_file_supabase(file_url, bucket)


async def _download_file_supabase(file_url: str, bucket: str | None = None) -> bytes:
    """Download a file from Supabase Storage by its public URL."""
    from ..core.config import settings

    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    # Extract the storage path from the URL
    # URL format: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
    try:
        storage_path = file_url.split(f"/object/public/{bucket}/")[-1]
        client = _get_supabase_client()
        file_bytes: bytes = client.storage.from_(bucket).download(storage_path)
        logger.info(f"Downloaded file from Supabase Storage: {storage_path}")
        return file_bytes
    except Exception as e:
        logger.error(f"Supabase download failed: {e}")
        raise RuntimeError(f"File download failed: {e}") from e


async def _download_file_local(file_url: str, bucket: str | None = None) -> bytes:
    """Download a file from local storage."""
    # Get local storage base path
    base_path = _get_local_storage_path()

    # Determine storage directory (bucket for Supabase, subdirectory for local)
    storage_dir = bucket or "uploads"

    # Remove leading slash if present
    if file_url.startswith('/'):
        file_url = file_url[1:]

    # Construct the full file path
    file_path = os.path.join(base_path, storage_dir, file_url)

    # Check if file exists
    if not os.path.exists(file_path):
        raise RuntimeError(f"File not found: {file_url}")

    # Read and return the file
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    logger.info(f"Downloaded file from local storage: {file_url}")
    return file_bytes


async def delete_file(file_url: str, bucket: str | None = None) -> None:
    """
    Delete a file from storage (Supabase or local) by its URL/path.

    Parameters
    ----------
    file_url : str
        The public URL (for Supabase) or relative path (for local) of the file to delete.
    bucket : str | None
        Storage bucket name (for Supabase) or subdirectory (for local).
        Defaults to SUPABASE_STORAGE_BUCKET for Supabase or "uploads" for local.
    """
    # Check if we should use local storage
    if _should_use_local_storage():
        await _delete_file_local(file_url, bucket)
    else:
        await _delete_file_supabase(file_url, bucket)


async def _delete_file_supabase(file_url: str, bucket: str | None = None) -> None:
    """Delete a file from Supabase Storage by its public URL."""
    from ..core.config import settings

    bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    try:
        storage_path = file_url.split(f"/object/public/{bucket}/")[-1]
        client = _get_supabase_client()
        client.storage.from_(bucket).remove([storage_path])
        logger.info(f"Deleted file from Supabase Storage: {storage_path}")
    except Exception as e:
        logger.error(f"Supabase delete failed: {e}")
        raise RuntimeError(f"File deletion failed: {e}") from e


async def _delete_file_local(file_url: str, bucket: str | None = None) -> None:
    """Delete a file from local storage."""
    # Get local storage base path
    base_path = _get_local_storage_path()

    # Determine storage directory (bucket for Supabase, subdirectory for local)
    storage_dir = bucket or "uploads"

    # Remove leading slash if present
    if file_url.startswith('/'):
        file_url = file_url[1:]

    # Construct the full file path
    file_path = os.path.join(base_path, storage_dir, file_url)

    # Check if file exists
    if not os.path.exists(file_path):
        raise RuntimeError(f"File not found: {file_url}")

    # Remove the file
    os.remove(file_path)
    logger.info(f"Deleted file from local storage: {file_url}")