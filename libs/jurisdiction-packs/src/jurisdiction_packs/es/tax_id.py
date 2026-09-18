from jurisdiction_packs.protocol import ValidationResult

NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
CIF_CONTROL_LETTERS = "JABCDEFGHI"
CIF_LETTER_CONTROL_ENTITIES = "KPQS"
CIF_DIGIT_CONTROL_ENTITIES = "ABEH"


def generate_valid_nif(number: int) -> str:
    number = number % 100_000_000
    letter = NIF_LETTERS[number % 23]
    return f"{number:08d}{letter}"


def validate_nif(nif: str) -> ValidationResult:
    if len(nif) != 9 or not nif[:8].isdigit() or not nif[8].isalpha():
        return ValidationResult(is_valid=False, reason="NIF must be 8 digits + letter")
    expected_letter = NIF_LETTERS[int(nif[:8]) % 23]
    if nif[8].upper() != expected_letter:
        return ValidationResult(is_valid=False, reason="control letter mismatch")
    return ValidationResult(is_valid=True)


def cif_control_digit(digits7: str) -> int:
    total = 0
    for i, ch in enumerate(digits7):
        digit = int(ch)
        if i % 2 == 0:
            doubled = digit * 2
            total += doubled // 10 + doubled % 10
        else:
            total += digit
    return (10 - (total % 10)) % 10


def generate_valid_cif(letter: str, digits7: str) -> str:
    control_digit = cif_control_digit(digits7)
    if letter in CIF_LETTER_CONTROL_ENTITIES:
        control_char = CIF_CONTROL_LETTERS[control_digit]
    else:
        control_char = str(control_digit)
    return letter + digits7 + control_char


def validate_cif(cif: str) -> ValidationResult:
    if len(cif) != 9 or not cif[0].isalpha() or not cif[1:8].isdigit():
        return ValidationResult(
            is_valid=False, reason="CIF must be a letter + 7 digits + control char"
        )
    letter = cif[0].upper()
    control_char = cif[8].upper()
    control_digit = cif_control_digit(cif[1:8])
    if letter in CIF_LETTER_CONTROL_ENTITIES:
        valid = control_char == CIF_CONTROL_LETTERS[control_digit]
    elif letter in CIF_DIGIT_CONTROL_ENTITIES:
        valid = control_char == str(control_digit)
    else:
        valid = control_char in {str(control_digit), CIF_CONTROL_LETTERS[control_digit]}
    if not valid:
        return ValidationResult(is_valid=False, reason="control character mismatch")
    return ValidationResult(is_valid=True)
