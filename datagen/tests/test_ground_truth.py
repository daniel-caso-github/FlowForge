from datetime import date
from decimal import Decimal

from datagen.ground_truth import build_invoice
from datagen.master_data import generate_master_data
from jurisdiction_packs.es.pack import SpainJurisdictionPack
from jurisdiction_packs.pe.pack import PeruJurisdictionPack


def test_pe_invoice_with_detraction_is_arithmetically_consistent():
    world = generate_master_data(seed=42)
    company = next(c for c in world.companies if c.jurisdiction == "PE")
    supplier = next(s for s in world.suppliers if s.jurisdiction == "PE" and s.profile.detraction_rate)
    products = [p for p in world.products if p.currency == "PEN"][:1]
    pack = PeruJurisdictionPack()

    invoice = build_invoice(pack, company, supplier, products, "F001-1", date(2026, 1, 15))

    tax_total = sum((t.amount.amount for t in invoice.taxes), Decimal("0"))
    assert invoice.total.original.amount == invoice.subtotal.original.amount + tax_total
    withholding_total = sum((w.amount.amount for w in invoice.withholdings), Decimal("0"))
    assert invoice.payable.amount == invoice.total.original.amount - withholding_total
    assert len(invoice.withholdings) == 1
    assert invoice.withholdings[0].kind == "detraction"


def test_es_invoice_without_irpf_is_arithmetically_consistent():
    world = generate_master_data(seed=42)
    company = next(c for c in world.companies if c.jurisdiction == "ES")
    supplier = next(s for s in world.suppliers if s.jurisdiction == "ES" and not s.profile.subject_to_irpf)
    products = [p for p in world.products if p.currency == "EUR"][:1]
    pack = SpainJurisdictionPack()

    invoice = build_invoice(pack, company, supplier, products, "F001-1", date(2026, 1, 15))

    tax_total = sum((t.amount.amount for t in invoice.taxes), Decimal("0"))
    assert invoice.total.original.amount == invoice.subtotal.original.amount + tax_total
    assert invoice.payable.amount == invoice.total.original.amount
    assert invoice.withholdings == []


def test_invoice_key_combines_company_supplier_and_series():
    world = generate_master_data(seed=42)
    company = world.companies[0]
    supplier = next(s for s in world.suppliers if s.jurisdiction == company.jurisdiction)
    currency = "PEN" if company.jurisdiction == "PE" else "EUR"
    products = [p for p in world.products if p.currency == currency][:1]
    pack = PeruJurisdictionPack() if company.jurisdiction == "PE" else SpainJurisdictionPack()

    invoice = build_invoice(pack, company, supplier, products, "F001-1", date(2026, 1, 15))

    assert invoice.invoice_key == f"{company.id}:{supplier.tax_id}:F001-1"
