from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PortalStat(Base):
    """Optional manual override for a headline dashboard number. No row (or a null value) means: compute from data."""

    __tablename__ = "portal_stats"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    override_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
