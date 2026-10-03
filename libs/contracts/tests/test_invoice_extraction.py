from decimal import Decimal

from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.invoice_extraction import (
    BankAccountRefExtraction,
    ExtractionRunMetadata,
    InvoiceExtraction,
    InvoiceLineExtraction,
    TaxLineExtraction,
)
from flowforge_contracts.money import Money


def _field(value):
    return ExtractedField(value=value, evidence=str(value), page=1, confidence="high", signals=[])


def _sample_extraction() -> InvoiceExtraction:
    return InvoiceExtraction(
        supplier_tax_id=_field("81618495930"),
        series_number=_field("FPE-happy_path-0001"),
        issue_date=_field("2026-05-19"),
        due_date=_field("2026-06-18"),
        po_reference=_field(None),
        lines=[
            InvoiceLineExtraction(
                line_number=1,
                description=_field("Consultoria de software"),
                quantity=_field(Decimal("1")),
                unit_price=_field(Money(amount=Decimal("150.00"), currency="PEN")),
                line_total=_field(Money(amount=Decimal("150.00"), currency="PEN")),
            )
        ],
        subtotal=_field(Money(amount=Decimal("150.00"), currency="PEN")),
        taxes=[
            TaxLineExtraction(
                tax_type=_field("IGV"),
                rate=_field(Decimal("0.18")),
                base=_field(Money(amount=Decimal("150.00"), currency="PEN")),
                amount=_field(Money(amount=Decimal("27.00"), currency="PEN")),
            )
        ],
        withholdings=[],
        total=_field(Money(amount=Decimal("177.00"), currency="PEN")),
        bank_account=BankAccountRefExtraction(account_number=_field("10341316475255341983")),
    )


def test_invoice_extraction_round_trips_through_json():
    extraction = _sample_extraction()
    restored = InvoiceExtraction.model_validate_json(extraction.model_dump_json())
    assert restored == extraction


def test_invoice_extraction_allows_missing_optional_field():
    extraction = _sample_extraction()
    assert extraction.po_reference.value is None


def test_extraction_run_metadata_holds_cost_and_escalation():
    metadata = ExtractionRunMetadata(
        base_model="ff-base",
        escalated=True,
        escalation_model="ff-escalation",
        input_tokens=1200,
        output_tokens=300,
        cost_usd=Decimal("0.0123"),
        latency_ms=842,
    )
    assert metadata.escalated is True
    assert metadata.cost_usd == Decimal("0.0123")
