from decimal import Decimal

from pydantic import BaseModel

from flowforge_contracts.money import Money


class TaxLine(BaseModel):
    tax_type: str
    rate: Decimal
    base: Money
    amount: Money
