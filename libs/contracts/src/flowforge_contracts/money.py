from decimal import Decimal

from pydantic import BaseModel, Field


class Money(BaseModel):
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217 currency code")
