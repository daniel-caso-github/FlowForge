from datetime import date
from decimal import Decimal

from datagen.ground_truth import build_invoice
from datagen.master_data import generate_master_data
from datagen.scenarios import (
    build_credit_note,
    build_duplicate_pair,
    inject_invalid_tax_id,
    inject_missing_withholding,
    inject_multi_currency,
    inject_wrong_tax_calculation,
)
from jurisdiction_packs.pe.pack import PeruJurisdictionPack
from jurisdiction_packs.pe.tax_id import validate_ruc


def _pe_invoice(with_detraction: bool = True):
    world = generate_master_data(seed=42)
    company = next(c for c in world.companies if c.jurisdiction == "PE")
    supplier = next(
        s for s in world.suppliers
        if s.jurisdiction == "PE" and bool(s.profile.detraction_rate) == with_detraction
    )
    products = [p for p in world.products if p.currency == "PEN"][:1]
    pack = PeruJurisdictionPack()
    return pack, build_invoice(pack, company, supplier, products, "F001-1", date(2026, 1, 15))


def test_inject_wrong_tax_calculation_differs_from_expected():
    pack, invoice = _pe_invoice()
    tampered = inject_wrong_tax_calculation(invoice)
    expected = pack.expected_taxes(tampered)
    assert tampered.taxes[0].amount.amount != expected[0].amount.amount


def test_inject_missing_withholding_removes_the_expected_withholding():
    _, invoice = _pe_invoice(with_detraction=True)
    assert invoice.withholdings != []
    tampered = inject_missing_withholding(invoice)
    assert tampered.withholdings == []
    assert tampered.payable.amount == tampered.total.original.amount


def test_inject_invalid_tax_id_fails_validation():
    _, invoice = _pe_invoice()
    tampered = inject_invalid_tax_id(invoice)
    assert validate_ruc(tampered.supplier_tax_id).is_valid is False


def test_inject_multi_currency_converts_at_the_given_rate():
    _, invoice = _pe_invoice()
    tampered = inject_multi_currency(invoice, rate=Decimal("3.75"), foreign_currency="USD")
    assert tampered.subtotal.original.currency == "USD"
    assert tampered.subtotal.rate == Decimal("3.75")


def test_build_credit_note_full_covers_all_lines():
    _, invoice = _pe_invoice()
    credit_note = build_credit_note(invoice, scope="full")
    assert credit_note.scope == "full"
    assert credit_note.references_invoice_key == invoice.invoice_key
    assert len(credit_note.lines) == len(invoice.lines)


def test_build_duplicate_pair_shares_amounts_but_differs_in_key():
    _, invoice = _pe_invoice()
    original, duplicate = build_duplicate_pair(invoice)
    assert original.invoice_key != duplicate.invoice_key
    assert original.payable.amount == duplicate.payable.amount
