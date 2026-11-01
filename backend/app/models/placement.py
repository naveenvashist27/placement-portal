from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import PlacementStatus


class PlacementRecord(Base):
    __tablename__ = "placements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    company_year_id: Mapped[int] = mapped_column(ForeignKey("company_years.id"), index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("company_roles.id"), nullable=True)
    package_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    placement_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    placement_status: Mapped[PlacementStatus] = mapped_column(Enum(PlacementStatus), default=PlacementStatus.OFFERED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
