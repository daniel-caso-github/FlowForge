from jurisdiction_packs.protocol import ValidationResult


def cci_check_digits(first18: str) -> str:
    total = sum(int(d) * (i + 2) for i, d in enumerate(reversed(first18)))
    return f"{total % 97:02d}"


def generate_valid_cci(first18: str) -> str:
    return first18 + cci_check_digits(first18)


def validate_cci(cci: str) -> ValidationResult:
    if len(cci) != 20 or not cci.isdigit():
        return ValidationResult(is_valid=False, reason="CCI must be 20 digits")
    if cci[18:20] != cci_check_digits(cci[:18]):
        return ValidationResult(is_valid=False, reason="check digits mismatch")
    return ValidationResult(is_valid=True)
