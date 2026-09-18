from hypothesis import given
from hypothesis import strategies as st
from jurisdiction_packs.pe.bank_account import generate_valid_cci, validate_cci
from jurisdiction_packs.pe.tax_id import generate_valid_ruc, normalize_ruc, validate_ruc


def test_generate_valid_ruc_passes_validation():
    ruc = generate_valid_ruc("2012345678")
    assert len(ruc) == 11
    assert validate_ruc(ruc).is_valid is True


def test_validate_ruc_rejects_wrong_check_digit():
    ruc = generate_valid_ruc("2012345678")
    tampered = ruc[:10] + str((int(ruc[10]) + 1) % 10)
    assert validate_ruc(tampered).is_valid is False


def test_validate_ruc_rejects_wrong_length():
    assert validate_ruc("123").is_valid is False


def test_normalize_ruc_strips_non_digits():
    assert normalize_ruc("20-1234-5678-9") == "201234567 89".replace(" ", "")


@given(st.text(alphabet="0123456789", min_size=10, max_size=10))
def test_property_any_generated_ruc_is_valid(first10: str):
    assert validate_ruc(generate_valid_ruc(first10)).is_valid is True


def test_generate_valid_cci_passes_validation():
    cci = generate_valid_cci("001199123456789012")
    assert len(cci) == 20
    assert validate_cci(cci).is_valid is True


def test_validate_cci_rejects_wrong_check_digits():
    cci = generate_valid_cci("001199123456789012")
    tampered = cci[:18] + "99"
    assert validate_cci(tampered).is_valid is (tampered[18:20] == cci[18:20])


@given(st.text(alphabet="0123456789", min_size=18, max_size=18))
def test_property_any_generated_cci_is_valid(first18: str):
    assert validate_cci(generate_valid_cci(first18)).is_valid is True
