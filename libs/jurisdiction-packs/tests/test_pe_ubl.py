from datetime import date
from decimal import Decimal
from uuid import uuid4

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from hypothesis import given
from hypothesis import strategies as st
from jurisdiction_packs.pe.ubl import generate_xml, parse_structured


def _money(amount: str) -> Money:
    return Money(amount=Decimal(amount), currency="PEN")


def _converted(amount: str) -> ConvertedMoney:
    return ConvertedMoney(
        original=_money(amount), base=_money(amount), rate=Decimal("1"),
        rate_date=date(2026, 1, 15), rate_source="datagen-simulated",
    )


def _sample_invoice() -> CanonicalInvoice:
    return CanonicalInvoice(
        invoice_key="company-1:20123456789:F001-1", company_id=uuid4(), jurisdiction="PE",
        supplier_tax_id="20123456789", series_number="F001-1", issue_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15), po_reference="PO-123",
        lines=[
            InvoiceLine(
                line_number=1, description="Consulting", quantity=Decimal("1"),
                unit_price=_money("100.00"), line_total=_money("100.00"),
            )
        ],
        subtotal=_converted("100.00"),
        taxes=[
            TaxLine(tax_type="IGV", rate=Decimal("0.18"), base=_money("100.00"), amount=_money("18.00"))
        ],
        withholdings=[],
        total=_converted("118.00"),
        payable=_money("118.00"),
        bank_account=BankAccountRef(last4="1234", fingerprint="abc", account_number="0" * 20),
        source_extraction_id=uuid4(),
    )


def test_round_trip_reconstructs_the_same_invoice():
    original = _sample_invoice()
    restored = parse_structured(generate_xml(original))
    assert restored == original


def test_generated_xml_uses_the_real_ubl_namespace():
    xml = generate_xml(_sample_invoice())
    assert b"urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" in xml


@given(
    quantity=st.decimals(min_value="1", max_value="100", places=0),
    unit_price=st.decimals(min_value="1.00", max_value="9999.99", places=2),
)
def test_property_round_trip_survives_varying_line_amounts(quantity, unit_price):
    line_total = quantity * unit_price
    invoice = _sample_invoice().model_copy(
        update={
            "lines": [
                InvoiceLine(
                    line_number=1, description="Consulting", quantity=quantity,
                    unit_price=Money(amount=unit_price, currency="PEN"),
                    line_total=Money(amount=line_total, currency="PEN"),
                )
            ]
        }
    )
    restored = parse_structured(generate_xml(invoice))
    assert restored.lines == invoice.lines
