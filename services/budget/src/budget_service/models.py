from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from budget_service.db import Base


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"

    idempotency_key: Mapped[str] = mapped_column(String, primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    company_id: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="reserved")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
