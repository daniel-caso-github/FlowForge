from datetime import date
from decimal import Decimal
from uuid import uuid4

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from jurisdiction_packs.pe.pack import PeruJurisdictionPack
from jurisdiction_packs.pe.tax_id import generate_valid_ruc
from jurisdiction_packs.profiles import SupplierProfile


def _money(amount: str) -> Money:
    return Money(amount=Decimal(amount), currency="PEN")


def _converted(amount: str) -> ConvertedMoney:
    return ConvertedMoney(
        original=_money(amount), base=_money(amount), rate=Decimal("1"),
        rate_date=date(2026, 1, 15), rate_source="datagen-simulated",
    )


def _invoice_with_subtotal(amount: str) -> CanonicalInvoice:
    return CanonicalInvoice(
        invoice_key="k", company_id=uuid4(), jurisdiction="PE",
        supplier_tax_id=generate_valid_ruc("2012345678"), series_number="F001-1",
        issue_date=date(2026, 1, 15), due_date=None, po_reference=None,
        lines=[
            InvoiceLine(line_number=1, description="Consulting", quantity=Decimal("1"),
                        unit_price=_money(amount), line_total=_money(amount))
        ],
        subtotal=_converted(amount), taxes=[], withholdings=[],
        total=_converted(amount), payable=_money(amount),
        bank_account=BankAccountRef(last4="1234", fingerprint="x", account_number="0" * 20),
        source_extraction_id=uuid4(),
    )


def test_pack_code_is_pe():
    assert PeruJurisdictionPack().code == "PE"


def test_expected_taxes_computes_igv_at_18_percent():
    pack = PeruJurisdictionPack()
    taxes = pack.expected_taxes(_invoice_with_subtotal("100.00"))
    assert len(taxes) == 1
    assert taxes[0].tax_type == "IGV"
    assert taxes[0].amount.amount == Decimal("18.00")


def test_withholdings_returns_empty_when_supplier_has_no_detraction_rate():
    pack = PeruJurisdictionPack()
    supplier = SupplierProfile(tax_id="20123456789")
    result = pack.withholdings(_invoice_with_subtotal("100.00"), supplier, None)
    assert result == []


def test_withholdings_computes_detraction_when_supplier_has_a_rate():
    pack = PeruJurisdictionPack()
    supplier = SupplierProfile(tax_id="20123456789", detraction_rate=Decimal("0.12"))
    invoice = _invoice_with_subtotal("100.00")
    result = pack.withholdings(invoice, supplier, None)
    assert len(result) == 1
    assert result[0].kind == "detraction"
    assert result[0].amount.amount == Decimal("12.00")


def test_generate_xml_and_parse_structured_round_trip_through_the_pack():
    pack = PeruJurisdictionPack()
    invoice = _invoice_with_subtotal("100.00")
    restored = pack.parse_structured(pack.generate_xml(invoice))
    assert restored == invoice


def test_validate_tax_id_delegates_to_ruc_validation():
    pack = PeruJurisdictionPack()
    valid_ruc = generate_valid_ruc("2012345678")
    tampered = valid_ruc[:10] + str((int(valid_ruc[10]) + 1) % 10)
    assert pack.validate_tax_id(valid_ruc).is_valid is True
    assert pack.validate_tax_id(tampered).is_valid is False
