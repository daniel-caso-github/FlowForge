from jurisdiction_packs.protocol import ValidationResult

RUC_WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def ruc_check_digit(first10: str) -> int:
    total = sum(int(d) * w for d, w in zip(first10, RUC_WEIGHTS, strict=True))
    remainder = total % 11
    check = 11 - remainder
    if check == 11:
        check = 0
    elif check == 10:
        check = 1
    return check


def generate_valid_ruc(first10: str) -> str:
    return first10 + str(ruc_check_digit(first10))


def normalize_ruc(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())


def validate_ruc(ruc: str) -> ValidationResult:
    if len(ruc) != 11 or not ruc.isdigit():
        return ValidationResult(is_valid=False, reason="RUC must be 11 digits")
    if int(ruc[10]) != ruc_check_digit(ruc[:10]):
        return ValidationResult(is_valid=False, reason="check digit mismatch")
    return ValidationResult(is_valid=True)
