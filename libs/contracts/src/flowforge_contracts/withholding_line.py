from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from flowforge_contracts.money import Money


class WithholdingLine(BaseModel):
    kind: Literal["detraction", "igv_retention", "irpf"]
    rate: Decimal
    amount: Money
    code: str | None = None
