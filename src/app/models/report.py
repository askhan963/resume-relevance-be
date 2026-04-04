from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """
    Stores the full AI analysis result for a Resume + JobDescription pair.
    Includes relevance score, ATS score, keyword analysis, recommendations,
    and optionally the AI-rewritten resume.
    """

    __tablename__ = "report"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id"), index=True, nullable=False)
    job_description_id: Mapped[int] = mapped_column(ForeignKey("job_description.id"), index=True, nullable=False)

    # Analysis status
    status: Mapped[str] = mapped_column(String(20), default=ReportStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)

    # Scores
    relevance_score: Mapped[float | None] = mapped_column(Float, default=None)
    ats_score: Mapped[float | None] = mapped_column(Float, default=None)

    # Keyword analysis (stored as JSON arrays)
    matched_keywords: Mapped[list | None] = mapped_column(JSONB, default=None)
    missing_keywords: Mapped[list | None] = mapped_column(JSONB, default=None)

    # Recommendations (stored as JSON array of strings)
    recommendations: Mapped[list | None] = mapped_column(JSONB, default=None)

    # AI rewrite results (populated after rewrite is requested)
    optimized_resume_text: Mapped[str | None] = mapped_column(Text, default=None)
    optimized_file_url: Mapped[str | None] = mapped_column(String(1000), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
