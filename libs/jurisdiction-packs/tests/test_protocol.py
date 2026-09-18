from jurisdiction_packs.protocol import (
    CreditNoteKind,
    ExchangeRateRule,
    RoundingPolicy,
    ValidationResult,
)


def test_validation_result_holds_reason_on_failure():
    result = ValidationResult(is_valid=False, reason="check digit mismatch")
    assert result.is_valid is False
    assert result.reason == "check digit mismatch"


def test_rounding_policy_holds_decimal_places_and_mode():
    policy = RoundingPolicy(decimal_places=2, rounding_mode="ROUND_HALF_UP")
    assert policy.decimal_places == 2


def test_exchange_rate_rule_holds_source_and_as_of():
    rule = ExchangeRateRule(rate_source="datagen-simulated", as_of="issue_date")
    assert rule.as_of == "issue_date"


def test_credit_note_kind_accepts_full_and_partial():
    values: list[CreditNoteKind] = ["full", "partial"]
    assert values == ["full", "partial"]
