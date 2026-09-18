from decimal import Decimal

from pydantic import BaseModel

from flowforge_contracts.money import Money


class InvoiceLine(BaseModel):
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Money
    line_total: Money
