from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class JobDescription(Base):
    """
    Stores job descriptions — either pasted as text or uploaded as a file.
    A user can save multiple JDs to compare against resumes.
    """

    __tablename__ = "job_description"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)

    # Content — always stored as raw text (extracted if uploaded as file)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Job info
    title: Mapped[str | None] = mapped_column(String(255), default=None)
    company: Mapped[str | None] = mapped_column(String(255), default=None)

    # Source tracking
    source: Mapped[str] = mapped_column(String(20), default="pasted")  # "pasted" or "uploaded"
    file_url: Mapped[str | None] = mapped_column(String(1000), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
