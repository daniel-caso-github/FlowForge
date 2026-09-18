from datetime import date
from decimal import Decimal
from uuid import uuid4

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from jurisdiction_packs.es.pack import SpainJurisdictionPack
from jurisdiction_packs.es.tax_id import generate_valid_cif
from jurisdiction_packs.profiles import SupplierProfile


def _money(amount: str) -> Money:
    return Money(amount=Decimal(amount), currency="EUR")


def _converted(amount: str) -> ConvertedMoney:
    return ConvertedMoney(
        original=_money(amount), base=_money(amount), rate=Decimal("1"),
        rate_date=date(2026, 1, 15), rate_source="datagen-simulated",
    )


def _invoice_with_subtotal(amount: str) -> CanonicalInvoice:
    return CanonicalInvoice(
        invoice_key="k", company_id=uuid4(), jurisdiction="ES",
        supplier_tax_id=generate_valid_cif("B", "1234567"), series_number="F001-1",
        issue_date=date(2026, 1, 15), due_date=None, po_reference=None,
        lines=[
            InvoiceLine(line_number=1, description="Consulting", quantity=Decimal("1"),
                        unit_price=_money(amount), line_total=_money(amount))
        ],
        subtotal=_converted(amount), taxes=[], withholdings=[],
        total=_converted(amount), payable=_money(amount),
        bank_account=BankAccountRef(
            last4="1234", fingerprint="x", account_number="ES00" + "0" * 20
        ),
        source_extraction_id=uuid4(),
    )


def test_pack_code_is_es():
    assert SpainJurisdictionPack().code == "ES"


def test_expected_taxes_computes_iva_at_21_percent():
    pack = SpainJurisdictionPack()
    taxes = pack.expected_taxes(_invoice_with_subtotal("100.00"))
    assert len(taxes) == 1
    assert taxes[0].tax_type == "IVA"
    assert taxes[0].amount.amount == Decimal("21.00")


def test_withholdings_returns_empty_when_supplier_not_subject_to_irpf():
    pack = SpainJurisdictionPack()
    supplier = SupplierProfile(tax_id="B12345674")
    assert pack.withholdings(_invoice_with_subtotal("100.00"), supplier, None) == []


def test_withholdings_computes_irpf_when_supplier_is_subject_to_it():
    pack = SpainJurisdictionPack()
    supplier = SupplierProfile(tax_id="B12345674", subject_to_irpf=True, irpf_rate=Decimal("0.15"))
    invoice = _invoice_with_subtotal("100.00")
    result = pack.withholdings(invoice, supplier, None)
    assert len(result) == 1
    assert result[0].kind == "irpf"
    assert result[0].amount.amount == Decimal("15.00")


def test_generate_xml_and_parse_structured_round_trip_through_the_pack():
    pack = SpainJurisdictionPack()
    invoice = _invoice_with_subtotal("100.00")
    restored = pack.parse_structured(pack.generate_xml(invoice))
    assert restored == invoice


def test_validate_tax_id_dispatches_cif_and_nif():
    pack = SpainJurisdictionPack()
    assert pack.validate_tax_id(generate_valid_cif("B", "1234567")).is_valid is True
    assert pack.validate_tax_id("00000000A").is_valid is False
