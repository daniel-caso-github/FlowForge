from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from datagen.rendering import render_credit_note_pdf, render_invoice_pdf
from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from pypdf import PdfReader


def _money(amount: str, currency: str) -> Money:
    return Money(amount=Decimal(amount), currency=currency)


def _converted(amount: str, currency: str) -> ConvertedMoney:
    return ConvertedMoney(
        original=_money(amount, currency), base=_money(amount, currency),
        rate=Decimal("1"), rate_date=date(2026, 5, 19), rate_source="test",
    )


def _sample_invoice() -> CanonicalInvoice:
    return CanonicalInvoice(
        invoice_key="test-key", company_id=uuid4(), jurisdiction="PE",
        supplier_tax_id="81618495930", series_number="FPE-test-0001",
        issue_date=date(2026, 5, 19),
        lines=[InvoiceLine(
            line_number=1, description="Consultoria de software",
            quantity=Decimal("1"), unit_price=_money("150.00", "PEN"),
            line_total=_money("150.00", "PEN"),
        )],
        subtotal=_converted("150.00", "PEN"),
        taxes=[TaxLine(
            tax_type="IGV", rate=Decimal("0.18"),
            base=_money("150.00", "PEN"), amount=_money("27.00", "PEN"),
        )],
        withholdings=[],
        total=_converted("177.00", "PEN"),
        payable=_money("177.00", "PEN"),
        bank_account=BankAccountRef(
            last4="1983", fingerprint="abc123", account_number="10341316475255341983",
        ),
        source_extraction_id=uuid4(),
    )


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "".join(page.extract_text() for page in reader.pages)


def test_render_invoice_pdf_produces_valid_pdf_with_text_layer():
    pdf_bytes = render_invoice_pdf(
        _sample_invoice(), supplier_name="Consultora Lima SAC", company_name="Andina Retail S.A.C.",
    )
    assert pdf_bytes.startswith(b"%PDF-")
    text = _extract_text(pdf_bytes)
    assert "81618495930" in text
    assert "FPE-test-0001" in text


def test_render_invoice_pdf_is_deterministic():
    invoice = _sample_invoice()
    supplier = "Consultora Lima SAC"
    company = "Andina Retail S.A.C."
    first = render_invoice_pdf(invoice, supplier_name=supplier, company_name=company)
    second = render_invoice_pdf(invoice, supplier_name=supplier, company_name=company)
    assert first == second


def _sample_credit_note() -> CanonicalCreditNote:
    return CanonicalCreditNote(
        credit_note_key="test-cn-key", references_invoice_key="test-key",
        scope="full", reason_code="return",
        lines=[InvoiceLine(
            line_number=1, description="Consultoria de software",
            quantity=Decimal("1"), unit_price=_money("150.00", "PEN"),
            line_total=_money("150.00", "PEN"),
        )],
        total=_converted("177.00", "PEN"),
    )


def test_render_credit_note_pdf_produces_valid_pdf_with_text_layer():
    pdf_bytes = render_credit_note_pdf(
        _sample_credit_note(), supplier_name="Consultora Lima SAC",
        company_name="Andina Retail S.A.C.", jurisdiction="PE",
    )
    assert pdf_bytes.startswith(b"%PDF-")
    text = _extract_text(pdf_bytes)
    assert "test-cn-key" in text
    assert "test-key" in text


def test_render_credit_note_pdf_is_deterministic():
    credit_note = _sample_credit_note()
    first = render_credit_note_pdf(
        credit_note, supplier_name="Consultora Lima SAC",
        company_name="Andina Retail S.A.C.", jurisdiction="PE",
    )
    second = render_credit_note_pdf(
        credit_note, supplier_name="Consultora Lima SAC",
        company_name="Andina Retail S.A.C.", jurisdiction="PE",
    )
    assert first == second
