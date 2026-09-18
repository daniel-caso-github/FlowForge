from pydantic import BaseModel

from flowforge_contracts.money import Money


class ReserveBudgetRequest(BaseModel):
    idempotency_key: str
    invoice_id: str
    company_id: str
    amount: Money


class ReserveBudgetResponse(BaseModel):
    idempotency_key: str
    status: str


class ReleaseBudgetRequest(BaseModel):
    idempotency_key: str
