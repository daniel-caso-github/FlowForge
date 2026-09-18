from datagen.master_data import generate_master_data
from jurisdiction_packs.es.tax_id import validate_cif
from jurisdiction_packs.pe.bank_account import validate_cci
from jurisdiction_packs.pe.tax_id import validate_ruc


def test_generate_master_data_is_deterministic():
    first = generate_master_data(seed=42)
    second = generate_master_data(seed=42)
    assert [c.tax_id for c in first.companies] == [c.tax_id for c in second.companies]
    assert [s.tax_id for s in first.suppliers] == [s.tax_id for s in second.suppliers]


def test_every_pe_supplier_has_a_valid_ruc_and_cci():
    world = generate_master_data(seed=42)
    for supplier in world.suppliers:
        if supplier.jurisdiction != "PE":
            continue
        assert validate_ruc(supplier.tax_id).is_valid is True
        assert validate_cci(supplier.bank_account_number).is_valid is True


def test_every_es_supplier_has_a_valid_cif():
    world = generate_master_data(seed=42)
    for supplier in world.suppliers:
        if supplier.jurisdiction != "ES":
            continue
        assert validate_cif(supplier.tax_id).is_valid is True


def test_at_least_one_supplier_per_jurisdiction_has_a_withholding_rate():
    world = generate_master_data(seed=42)
    pe_with_detraction = [
        s for s in world.suppliers if s.jurisdiction == "PE" and s.profile.detraction_rate
    ]
    es_with_irpf = [
        s for s in world.suppliers if s.jurisdiction == "ES" and s.profile.subject_to_irpf
    ]
    assert pe_with_detraction
    assert es_with_irpf


def test_both_jurisdictions_have_at_least_one_company_and_product():
    world = generate_master_data(seed=42)
    assert any(c.jurisdiction == "PE" for c in world.companies)
    assert any(c.jurisdiction == "ES" for c in world.companies)
    assert any(p.currency == "PEN" for p in world.products)
    assert any(p.currency == "EUR" for p in world.products)
