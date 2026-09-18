import random
from datetime import date
from decimal import Decimal
from uuid import uuid4

from datagen.degradation import degrade, reindent, swap_namespace_prefixes
from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from jurisdiction_packs.pe.ubl import generate_xml, parse_structured


def _sample_invoice() -> CanonicalInvoice:
    money = Money(amount=Decimal("100.00"), currency="PEN")
    converted = ConvertedMoney(
        original=money, base=money, rate=Decimal("1"), rate_date=date(2026, 1, 15),
        rate_source="datagen-simulated",
    )
    return CanonicalInvoice(
        invoice_key="k", company_id=uuid4(), jurisdiction="PE", supplier_tax_id="20123456789",
        series_number="F001-1", issue_date=date(2026, 1, 15), due_date=None, po_reference=None,
        lines=[
            InvoiceLine(line_number=1, description="Consulting", quantity=Decimal("1"),
                        unit_price=money, line_total=money)
        ],
        subtotal=converted, taxes=[], withholdings=[], total=converted, payable=money,
        bank_account=BankAccountRef(last4="1234", fingerprint="x", account_number="0" * 20),
        source_extraction_id=uuid4(),
    )


def test_reindent_still_parses_to_the_same_invoice():
    original = _sample_invoice()
    xml = reindent(generate_xml(original))
    assert parse_structured(xml) == original


def test_swap_namespace_prefixes_still_parses_to_the_same_invoice():
    original = _sample_invoice()
    xml = swap_namespace_prefixes(generate_xml(original))
    assert parse_structured(xml) == original


def test_degrade_never_breaks_parsing_across_many_seeds():
    original = _sample_invoice()
    for seed in range(20):
        xml = degrade(generate_xml(original), random.Random(seed))
        assert parse_structured(xml) == original
