from datetime import UTC, datetime
from decimal import Decimal

from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.invoice_extraction import (
    BankAccountRefExtraction,
    ExtractionRunMetadata,
    InvoiceExtraction,
)
from flowforge_contracts.money import Money
from invoice_service.api.mappers import to_extraction_response
from invoice_service.domain.extraction import Extraction


def _field(value):
    return ExtractedField(value=value, evidence=None, page=None, confidence="high", signals=[])


def test_to_extraction_response_maps_every_field():
    extraction = Extraction(
        idempotency_key="doc-1-attempt-1",
        document_id="doc-1",
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

    response = to_extraction_response(extraction)

    assert response.idempotency_key == "doc-1-attempt-1"
    assert response.document_id == "doc-1"
    assert response.extraction.supplier_tax_id.value == "81618495930"
    assert response.run_metadata.cost_usd == Decimal("0.001")
    assert response.created_at == datetime(2026, 5, 19, 12, 0, 0, tzinfo=UTC)
