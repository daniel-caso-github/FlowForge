from fastapi import APIRouter, Request
from flowforge_contracts.erp import ConfirmPaymentRequest, PostInvoiceRequest, SchedulePaymentRequest

router = APIRouter()


@router.post("/erp/invoices")
def post_invoice(request: PostInvoiceRequest, req: Request) -> dict:
    store = req.app.state.store
    status = store.post_invoice(request.idempotency_key, request.invoice_id, request.company_id)
    return {"idempotency_key": request.idempotency_key, "status": status}


@router.delete("/erp/invoices/{idempotency_key}")
def void_invoice(idempotency_key: str, req: Request) -> dict:
    store = req.app.state.store
    status = store.void_invoice(idempotency_key)
    return {"idempotency_key": idempotency_key, "status": status}


@router.post("/payments/schedule")
def schedule_payment(request: SchedulePaymentRequest, req: Request) -> dict:
    store = req.app.state.store
    status = store.schedule_payment(request.idempotency_key, request.invoice_id)
    return {"idempotency_key": request.idempotency_key, "status": status}


@router.post("/payments/confirm")
def confirm_payment(request: ConfirmPaymentRequest, req: Request) -> dict:
    store = req.app.state.store
    status = store.confirm_payment(request.idempotency_key)
    return {"idempotency_key": request.idempotency_key, "status": status}
