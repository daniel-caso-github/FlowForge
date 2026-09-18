from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from flowforge_contracts.money import Money


class ConvertedMoney(BaseModel):
    original: Money
    base: Money
    rate: Decimal
    rate_date: date
    rate_source: str
