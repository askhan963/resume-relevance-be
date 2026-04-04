"""
Auth Endpoints: Register, Login, Logout, Token Refresh

POST /api/v1/auth/register   — Create a new user account
POST /api/v1/auth/login      — Authenticate and receive access token
POST /api/v1/auth/logout     — Invalidate tokens
POST /api/v1/auth/refresh    — Exchange refresh token for new access token
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import BadRequestException, UnauthorizedException
from ...core.schemas import Token
from ...core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TokenType,
    authenticate_user,
    blacklist_tokens,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_token,
)
from ...crud.crud_users import crud_users
from ...schemas.user import UserCreate, UserCreateInternal, UserRead
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> UserRead:
    """
    Register a new user account.

    - **name**: Full display name
    - **username**: Unique lowercase alphanumeric username
    - **email**: Unique email address
    - **password**: Minimum 8 characters
    """
    # Check if email is already taken
    existing_email = await crud_users.exists(db, email=user_in.email)
    if existing_email:
        raise BadRequestException("An account with this email already exists.")

    # Check if username is already taken
    existing_username = await crud_users.exists(db, username=user_in.username)
    if existing_username:
        raise BadRequestException("This username is already taken.")

    # Hash password and create user
    internal_data = UserCreateInternal(
        name=user_in.name,
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    created_user = await crud_users.create(db, object=internal_data)
    return created_user


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    """
    Authenticate with username/email and password.

    Returns an access token (Bearer) and sets a secure HttpOnly refresh token cookie.
    """
    user = await authenticate_user(
        username_or_email=form_data.username,
        password=form_data.password,
        db=db,
    )
    if not user:
        raise UnauthorizedException("Incorrect username/email or password.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires,
    )
    refresh_token = await create_refresh_token(data={"sub": user["username"]})
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=max_age,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    response: Response,
) -> None:
    """
    Log out the current user by blacklisting both tokens.

    Clears the refresh token cookie.
    """
    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    refresh_token = request.cookies.get("refresh_token", "")

    if access_token and refresh_token:
        await blacklist_tokens(access_token, refresh_token, db)

    response.delete_cookie("refresh_token")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    """
    Exchange a valid refresh token (from cookie) for a new access token.
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise UnauthorizedException("Refresh token is missing.")

    user_data = await verify_token(refresh_token_value, TokenType.REFRESH, db)
    if not user_data:
        raise UnauthorizedException("Invalid or expired refresh token.")

    new_access_token = await create_access_token(data={"sub": user_data.username_or_email})
    return {"access_token": new_access_token, "token_type": "bearer"}
