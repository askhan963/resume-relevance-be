"""
User Profile Endpoints

GET    /api/v1/users/me             — Get current user's profile
PATCH  /api/v1/users/me             — Update current user's profile
DELETE /api/v1/users/me             — Delete own account (soft delete)
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import BadRequestException
from ...core.security import blacklist_token, oauth2_scheme
from ...crud.crud_users import crud_users
from ...schemas.user import UserDelete, UserRead, UserUpdate, UserUpdateInternal

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Get the authenticated user's profile.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(
    update_data: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """
    Update the authenticated user's profile.

    Only the fields provided will be updated (partial update).
    Email and username changes are validated for uniqueness.
    """
    user_id = current_user["id"]

    # Check email uniqueness if changing
    if update_data.email and update_data.email != current_user["email"]:
        if await crud_users.exists(db, email=update_data.email):
            raise BadRequestException("This email address is already registered.")

    # Check username uniqueness if changing
    if update_data.username and update_data.username != current_user["username"]:
        if await crud_users.exists(db, username=update_data.username):
            raise BadRequestException("This username is already taken.")

    internal_update = UserUpdateInternal(
        **update_data.model_dump(exclude_none=True),
        updated_at=datetime.now(UTC),
    )
    await crud_users.update(db, object=internal_update, id=user_id)

    # Return updated user
    updated_user = await crud_users.get(db, id=user_id, is_deleted=False)
    return updated_user


@router.delete("/me", status_code=204)
async def delete_me(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
) -> None:
    """
    Soft-delete the authenticated user's account.

    The access token is blacklisted immediately. The user's data is marked as
    deleted but not permanently removed from the database.
    """
    delete_data = UserDelete(is_deleted=True, deleted_at=datetime.now(UTC))
    await crud_users.update(db, object=delete_data, id=current_user["id"])
    await blacklist_token(token=token, db=db)
