from pydantic import BaseModel

from flowforge_contracts.money import Money


class PostInvoiceRequest(BaseModel):
    idempotency_key: str
    invoice_id: str
    company_id: str
    amount: Money


class SchedulePaymentRequest(BaseModel):
    idempotency_key: str
    invoice_id: str
    amount: Money


class ConfirmPaymentRequest(BaseModel):
    idempotency_key: str
    invoice_id: str
