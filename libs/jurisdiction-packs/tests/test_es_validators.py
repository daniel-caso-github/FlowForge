from hypothesis import given
from hypothesis import strategies as st
from jurisdiction_packs.es.bank_account import generate_valid_iban, validate_iban
from jurisdiction_packs.es.tax_id import (
    generate_valid_cif,
    generate_valid_nif,
    validate_cif,
    validate_nif,
)


def test_generate_valid_nif_passes_validation():
    nif = generate_valid_nif(12345678)
    assert len(nif) == 9
    assert validate_nif(nif).is_valid is True


def test_validate_nif_rejects_wrong_control_letter():
    nif = generate_valid_nif(12345678)
    wrong_letter = "A" if nif[8] != "A" else "B"
    assert validate_nif(nif[:8] + wrong_letter).is_valid is False


@given(st.integers(min_value=0, max_value=99_999_999))
def test_property_any_generated_nif_is_valid(number: int):
    assert validate_nif(generate_valid_nif(number)).is_valid is True


def test_generate_valid_cif_passes_validation_for_digit_control_letter():
    cif = generate_valid_cif("A", "1234567")
    assert len(cif) == 9
    assert validate_cif(cif).is_valid is True


def test_generate_valid_cif_passes_validation_for_letter_control_letter():
    cif = generate_valid_cif("K", "1234567")
    assert validate_cif(cif).is_valid is True


@given(st.text(alphabet="0123456789", min_size=7, max_size=7))
def test_property_any_generated_cif_is_valid(digits7: str):
    assert validate_cif(generate_valid_cif("A", digits7)).is_valid is True


def test_validate_iban_accepts_a_known_valid_spanish_iban():
    assert validate_iban("ES9121000418450200051332").is_valid is True


def test_validate_iban_rejects_tampered_checksum():
    assert validate_iban("ES9121000418450200051333").is_valid is False


def test_generate_valid_iban_passes_validation():
    assert generate_valid_iban("21000418450200051332") == "ES9121000418450200051332"


@given(st.text(alphabet="0123456789", min_size=20, max_size=20))
def test_property_any_generated_iban_is_valid(bban20: str):
    assert validate_iban(generate_valid_iban(bban20)).is_valid is True
