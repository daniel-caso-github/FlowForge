from decimal import Decimal

from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.invoice_extraction import (
    BankAccountRefExtraction,
    ExtractionRunMetadata,
    InvoiceExtraction,
)
from flowforge_contracts.money import Money
from invoice_service.application.commands.record_extraction import (
    RecordExtractionCommand,
    RecordExtractionCommandHandler,
)


def _field(value):
    return ExtractedField(value=value, evidence=None, page=None, confidence="high", signals=[])


def _sample_command(idempotency_key: str) -> RecordExtractionCommand:
    return RecordExtractionCommand(
        idempotency_key=idempotency_key,
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
    )


def test_record_extraction_creates_a_new_extraction(fake_repository):
    handler = RecordExtractionCommandHandler(fake_repository)

    extraction = handler.handle(_sample_command("doc-1-attempt-1"))

    assert extraction.idempotency_key == "doc-1-attempt-1"
    assert extraction.extraction.supplier_tax_id.value == "81618495930"


def test_record_extraction_is_idempotent_for_the_same_key(fake_repository):
    handler = RecordExtractionCommandHandler(fake_repository)
    command = _sample_command("doc-1-attempt-1")

    first = handler.handle(command)
    second = handler.handle(command)

    assert first == second
    assert len(fake_repository.extractions) == 1
