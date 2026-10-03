from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.extraction import RecordExtractionRequest
from flowforge_contracts.invoice_extraction import (
    BankAccountRefExtraction,
    ExtractionRunMetadata,
    InvoiceExtraction,
)
from flowforge_contracts.money import Money
from invoice_service.domain.extraction import Extraction
from invoice_service.infrastructure.db import Base, get_db
from invoice_service.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


class FakeExtractionRepository:
    def __init__(self) -> None:
        self.extractions: dict[str, Extraction] = {}

    def get(self, idempotency_key: str) -> Extraction | None:
        return self.extractions.get(idempotency_key)

    def list_by_document(self, document_id: str) -> list[Extraction]:
        return [e for e in self.extractions.values() if e.document_id == document_id]

    def add(self, extraction: Extraction) -> None:
        self.extractions[extraction.idempotency_key] = extraction


@pytest.fixture()
def fake_repository() -> FakeExtractionRepository:
    return FakeExtractionRepository()


def _field(value):
    return ExtractedField(value=value, evidence=None, page=None, confidence="high", signals=[])


@pytest.fixture()
def make_extraction_payload():
    def _make(idempotency_key: str, document_id: str = "doc-1") -> dict:
        request = RecordExtractionRequest(
            idempotency_key=idempotency_key,
            document_id=document_id,
            company_id="company-1",
            extraction=InvoiceExtraction(
                supplier_tax_id=_field("81618495930"),
                series_number=_field("FPE-happy_path-0001"),
                issue_date=_field("2026-05-19"),
                due_date=_field("2026-06-18"),
                po_reference=_field(None),
                lines=[],
                subtotal=_field(Money(amount=Decimal("150.00"), currency="PEN")),
                taxes=[],
                withholdings=[],
                total=_field(Money(amount=Decimal("177.00"), currency="PEN")),
                bank_account=BankAccountRefExtraction(
                    account_number=_field("10341316475255341983")
                ),
            ),
            run_metadata=ExtractionRunMetadata(
                base_model="ff-base", escalated=False, escalation_model=None,
                input_tokens=500, output_tokens=120, cost_usd=Decimal("0.001"), latency_ms=430,
            ),
        )
        return request.model_dump(mode="json")

    return _make


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
