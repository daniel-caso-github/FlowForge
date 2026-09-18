from jurisdiction_packs.protocol import ValidationResult


def generate_valid_iban(bban20: str) -> str:
    rearranged = bban20 + "ES00"
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    check = 98 - (int(numeric) % 97)
    return f"ES{check:02d}{bban20}"


def validate_iban(iban: str) -> ValidationResult:
    iban = iban.replace(" ", "").upper()
    if len(iban) != 24 or not iban.startswith("ES"):
        return ValidationResult(
            is_valid=False, reason="Spanish IBAN must be 24 chars starting with ES"
        )
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    if int(numeric) % 97 != 1:
        return ValidationResult(is_valid=False, reason="IBAN checksum failed")
    return ValidationResult(is_valid=True)
