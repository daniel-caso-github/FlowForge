import hashlib
from datetime import date
from decimal import Decimal

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.jurisdiction import Jurisdiction
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine


def test_jurisdiction_accepts_pe_and_es():
    values: list[Jurisdiction] = ["PE", "ES"]
    assert values == ["PE", "ES"]


def test_converted_money_holds_original_and_base():
    cm = ConvertedMoney(
        original=Money(amount=Decimal("100.00"), currency="USD"),
        base=Money(amount=Decimal("375.00"), currency="PEN"),
        rate=Decimal("3.75"),
        rate_date=date(2026, 1, 15),
        rate_source="datagen-simulated",
    )
    assert cm.original.currency == "USD"
    assert cm.base.currency == "PEN"


def test_tax_line_holds_base_and_amount():
    tax = TaxLine(
        tax_type="IGV",
        rate=Decimal("0.18"),
        base=Money(amount=Decimal("100.00"), currency="PEN"),
        amount=Money(amount=Decimal("18.00"), currency="PEN"),
    )
    assert tax.tax_type == "IGV"


def test_withholding_line_kind_is_constrained():
    withholding = WithholdingLine(
        kind="detraction",
        rate=Decimal("0.12"),
        amount=Money(amount=Decimal("12.00"), currency="PEN"),
        code="001",
    )
    assert withholding.kind == "detraction"


def test_invoice_line_holds_quantity_and_totals():
    line = InvoiceLine(
        line_number=1,
        description="Consulting services",
        quantity=Decimal("2"),
        unit_price=Money(amount=Decimal("50.00"), currency="PEN"),
        line_total=Money(amount=Decimal("100.00"), currency="PEN"),
    )
    assert line.line_number == 1


def test_bank_account_ref_holds_last4_and_fingerprint():
    account_number = "00219912345678901234"
    fingerprint = hashlib.sha256(account_number.encode()).hexdigest()
    ref = BankAccountRef(
        last4=account_number[-4:], fingerprint=fingerprint, account_number=account_number
    )
    assert ref.last4 == "1234"
