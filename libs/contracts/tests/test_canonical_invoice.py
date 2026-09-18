from datetime import date
from decimal import Decimal
from uuid import uuid4

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine


def _converted(amount: str, currency: str = "PEN") -> ConvertedMoney:
    money = Money(amount=Decimal(amount), currency=currency)
    return ConvertedMoney(
        original=money, base=money, rate=Decimal("1"), rate_date=date(2026, 1, 15),
        rate_source="datagen-simulated",
    )


def test_canonical_invoice_holds_lines_taxes_and_payable():
    invoice = CanonicalInvoice(
        invoice_key="company-1:20123456789:F001-1",
        company_id=uuid4(),
        jurisdiction="PE",
        supplier_tax_id="20123456789",
        series_number="F001-1",
        issue_date=date(2026, 1, 15),
        due_date=None,
        po_reference=None,
        lines=[
            InvoiceLine(
                line_number=1, description="Consulting", quantity=Decimal("1"),
                unit_price=Money(amount=Decimal("100.00"), currency="PEN"),
                line_total=Money(amount=Decimal("100.00"), currency="PEN"),
            )
        ],
        subtotal=_converted("100.00"),
        taxes=[
            TaxLine(
                tax_type="IGV", rate=Decimal("0.18"),
                base=Money(amount=Decimal("100.00"), currency="PEN"),
                amount=Money(amount=Decimal("18.00"), currency="PEN"),
            )
        ],
        withholdings=[],
        total=_converted("118.00"),
        payable=Money(amount=Decimal("118.00"), currency="PEN"),
        bank_account=BankAccountRef(last4="1234", fingerprint="abc", account_number="x" * 20),
        source_extraction_id=uuid4(),
    )
    assert invoice.jurisdiction == "PE"
    assert invoice.payable.amount == Decimal("118.00")


def test_canonical_credit_note_references_an_invoice():
    credit_note = CanonicalCreditNote(
        credit_note_key="company-1:20123456789:FC01-1",
        references_invoice_key="company-1:20123456789:F001-1",
        scope="full",
        reason_code="01",
        es_rectification_mode=None,
        lines=[],
        total=_converted("118.00"),
    )
    assert credit_note.scope == "full"
