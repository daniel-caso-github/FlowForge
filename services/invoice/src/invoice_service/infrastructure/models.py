from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from invoice_service.infrastructure.db import Base


class ExtractionModel(Base):
    __tablename__ = "extractions"

    idempotency_key: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, nullable=False)
    company_id: Mapped[str] = mapped_column(String, nullable=False)
    extraction: Mapped[dict] = mapped_column(JSON, nullable=False)
    base_model: Mapped[str] = mapped_column(String, nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    escalation_model: Mapped[str | None] = mapped_column(String, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
