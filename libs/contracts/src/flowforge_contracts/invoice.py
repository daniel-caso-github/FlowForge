from pydantic import BaseModel

from flowforge_contracts.money import Money


class InvoiceDemoPayload(BaseModel):
    invoice_id: str
    company_id: str
    amount: Money
    fail_at: str | None = None
    delay_at: str | None = None
    delay_seconds: int = 0
