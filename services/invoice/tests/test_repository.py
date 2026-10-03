from datetime import UTC, datetime
from decimal import Decimal

from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.invoice_extraction import (
    BankAccountRefExtraction,
    ExtractionRunMetadata,
    InvoiceExtraction,
)
from flowforge_contracts.money import Money
from invoice_service.domain.extraction import Extraction
from invoice_service.infrastructure.models import ExtractionModel
from invoice_service.infrastructure.repository import SqlAlchemyExtractionRepository, _to_domain


def _field(value):
    return ExtractedField(value=value, evidence=None, page=None, confidence="high", signals=[])


def _sample_extraction(idempotency_key: str, document_id: str) -> Extraction:
    return Extraction(
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
            bank_account=BankAccountRefExtraction(account_number=_field("10341316475255341983")),
        ),
        run_metadata=ExtractionRunMetadata(
            base_model="ff-base", escalated=False, escalation_model=None,
            input_tokens=500, output_tokens=120, cost_usd=Decimal("0.001"), latency_ms=430,
        ),
        created_at=datetime(2026, 5, 19, 12, 0, 0, tzinfo=UTC),
    )


def test_add_then_get_returns_the_same_extraction(db_session):
    repository = SqlAlchemyExtractionRepository(db_session)
    extraction = _sample_extraction("doc-1-attempt-1", "doc-1")

    repository.add(extraction)
    fetched = repository.get("doc-1-attempt-1")

    assert fetched is not None
    assert fetched.idempotency_key == "doc-1-attempt-1"
    assert fetched.extraction.supplier_tax_id.value == "81618495930"
    assert fetched.extraction.subtotal.value.amount == Decimal("150.00")
    assert fetched.run_metadata.cost_usd == Decimal("0.001")


def test_get_returns_none_for_unknown_key(db_session):
    repository = SqlAlchemyExtractionRepository(db_session)
    assert repository.get("missing") is None


def test_list_by_document_returns_all_extractions_for_that_document(db_session):
    repository = SqlAlchemyExtractionRepository(db_session)
    repository.add(_sample_extraction("doc-1-attempt-1", "doc-1"))
    repository.add(_sample_extraction("doc-1-attempt-2", "doc-1"))
    repository.add(_sample_extraction("doc-2-attempt-1", "doc-2"))

    results = repository.list_by_document("doc-1")

    assert len(results) == 2
    assert {r.idempotency_key for r in results} == {"doc-1-attempt-1", "doc-1-attempt-2"}


def test_to_domain_normalizes_naive_created_at_to_utc():
    sample = _sample_extraction("doc-1-attempt-1", "doc-1")
    record = ExtractionModel(
        idempotency_key=sample.idempotency_key,
        document_id=sample.document_id,
        company_id=sample.company_id,
        extraction=sample.extraction.model_dump(mode="json"),
        base_model=sample.run_metadata.base_model,
        escalated=sample.run_metadata.escalated,
        escalation_model=sample.run_metadata.escalation_model,
        input_tokens=sample.run_metadata.input_tokens,
        output_tokens=sample.run_metadata.output_tokens,
        cost_usd=sample.run_metadata.cost_usd,
        latency_ms=sample.run_metadata.latency_ms,
        created_at=datetime(2026, 5, 19, 12, 0, 0),
    )

    domain = _to_domain(record)

    assert domain.created_at.tzinfo is UTC


def test_to_domain_normalizes_padded_cost_usd():
    sample = _sample_extraction("doc-1-attempt-1", "doc-1")
    record = ExtractionModel(
        idempotency_key=sample.idempotency_key,
        document_id=sample.document_id,
        company_id=sample.company_id,
        extraction=sample.extraction.model_dump(mode="json"),
        base_model=sample.run_metadata.base_model,
        escalated=sample.run_metadata.escalated,
        escalation_model=sample.run_metadata.escalation_model,
        input_tokens=sample.run_metadata.input_tokens,
        output_tokens=sample.run_metadata.output_tokens,
        cost_usd=Decimal("0.0010000000"),
        latency_ms=sample.run_metadata.latency_ms,
        created_at=sample.created_at,
    )

    domain = _to_domain(record)

    assert domain.run_metadata.cost_usd == Decimal("0.001")
