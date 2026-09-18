from fastapi import APIRouter, Request
from flowforge_contracts.erp import PostInvoiceRequest

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
