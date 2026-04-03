from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100, examples=["Jane Doe"])]
    username: Annotated[str, Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$", examples=["jane_doe"])]
    email: Annotated[EmailStr, Field(examples=["jane.doe@example.com"])]


class User(TimestampSchema, UserBase, UUIDSchema, PersistentDeletion):
    profile_image_url: Annotated[str | None, Field(default=None)]
    hashed_password: str
    is_superuser: bool = False


class UserRead(BaseModel):
    """Public-facing user response schema."""

    id: int
    name: Annotated[str, Field(min_length=2, max_length=100, examples=["Jane Doe"])]
    username: Annotated[str, Field(min_length=2, max_length=50, examples=["jane_doe"])]
    email: Annotated[EmailStr, Field(examples=["jane.doe@example.com"])]
    profile_image_url: str | None = None


class UserCreate(UserBase):
    """Schema for registering a new user."""

    model_config = ConfigDict(extra="forbid")

    password: Annotated[
        str,
        Field(
            min_length=8,
            examples=["Str0ng!Pass"],
            description="Minimum 8 characters.",
        ),
    ]


class UserCreateInternal(UserBase):
    """Internal schema — stores hashed password."""

    hashed_password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(min_length=2, max_length=100, default=None)]
    username: Annotated[str | None, Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$", default=None)]
    email: Annotated[EmailStr | None, Field(default=None)]
    profile_image_url: Annotated[
        str | None,
        Field(pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", default=None),
    ]


class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool
