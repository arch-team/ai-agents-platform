"""Budget ORM 模型定义。"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base
from src.shared.infrastructure.utils import utc_now


class BudgetModel(Base):
    """Budget ORM 模型。"""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    used_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alert_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("department_id", "year", "month", name="uq_department_year_month"),
        CheckConstraint("year >= 2020 AND year <= 2100", name="ck_year_range"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_month_range"),
        CheckConstraint("budget_amount >= 0", name="ck_budget_amount_positive"),
        CheckConstraint("used_amount >= 0", name="ck_used_amount_positive"),
        CheckConstraint("alert_threshold >= 0 AND alert_threshold <= 1", name="ck_alert_threshold_range"),
    )
