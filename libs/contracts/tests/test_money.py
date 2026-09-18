from decimal import Decimal

import pytest
from pydantic import ValidationError

from flowforge_contracts.money import Money


def test_money_holds_amount_and_currency():
    money = Money(amount=Decimal("125.50"), currency="PEN")
    assert money.amount == Decimal("125.50")
    assert money.currency == "PEN"


def test_money_rejects_invalid_currency_length():
    with pytest.raises(ValidationError):
        Money(amount=Decimal("10.00"), currency="PENS")
