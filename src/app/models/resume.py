from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class Resume(Base):
    """
    Stores uploaded resumes and their extracted text content.
    A user can have multiple resumes.
    """

    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "pdf" or "docx"

    # Extracted content
    extracted_text: Mapped[str | None] = mapped_column(Text, default=None)

    # Scores cached from latest analysis (denormalized for quick access)
    latest_ats_score: Mapped[float | None] = mapped_column(default=None)
    latest_relevance_score: Mapped[float | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
