import asyncio
import os

import httpx
from flowforge_contracts.budget import ReleaseBudgetRequest, ReserveBudgetRequest
from flowforge_contracts.erp import ConfirmPaymentRequest, PostInvoiceRequest, SchedulePaymentRequest
from flowforge_contracts.invoice import InvoiceDemoPayload
from temporalio import activity
from temporalio.exceptions import ApplicationError

BUDGET_SERVICE_URL = os.environ.get("BUDGET_SERVICE_URL", "http://localhost:8001")
EXTERNAL_SIM_URL = os.environ.get("EXTERNAL_SIM_URL", "http://localhost:8002")


def _idempotency_key(workflow_id: str, activity_name: str) -> str:
    return f"{workflow_id}-{activity_name}"


def _maybe_inject_failure(payload: InvoiceDemoPayload, activity_name: str) -> None:
    if payload.fail_at == activity_name:
        raise ApplicationError(f"forced failure at {activity_name}", non_retryable=True)


async def _maybe_inject_delay(payload: InvoiceDemoPayload, activity_name: str) -> None:
    if payload.delay_at == activity_name:
        await asyncio.sleep(payload.delay_seconds)


@activity.defn
async def validate_invoice(payload: InvoiceDemoPayload) -> None:
    activity_name = "validate_invoice"
    _maybe_inject_failure(payload, activity_name)
    await _maybe_inject_delay(payload, activity_name)
    if payload.amount.amount <= 0:
        raise ApplicationError("invoice amount must be positive", non_retryable=True)


@activity.defn
async def reserve_budget(payload: InvoiceDemoPayload) -> None:
    activity_name = "reserve_budget"
    _maybe_inject_failure(payload, activity_name)
    await _maybe_inject_delay(payload, activity_name)
    workflow_id = activity.info().workflow_id
    request = ReserveBudgetRequest(
        idempotency_key=_idempotency_key(workflow_id, activity_name),
        invoice_id=payload.invoice_id,
        company_id=payload.company_id,
        amount=payload.amount,
    )
    async with httpx.AsyncClient(base_url=BUDGET_SERVICE_URL) as client:
        response = await client.post("/reservations", content=request.model_dump_json())
        response.raise_for_status()


@activity.defn
async def release_budget(payload: InvoiceDemoPayload) -> None:
    workflow_id = activity.info().workflow_id
    idempotency_key = _idempotency_key(workflow_id, "reserve_budget")
    request = ReleaseBudgetRequest(idempotency_key=idempotency_key)
    async with httpx.AsyncClient(base_url=BUDGET_SERVICE_URL) as client:
        response = await client.post(f"/reservations/{request.idempotency_key}/release")
        response.raise_for_status()


@activity.defn
async def post_to_erp(payload: InvoiceDemoPayload) -> None:
    activity_name = "post_to_erp"
    _maybe_inject_failure(payload, activity_name)
    await _maybe_inject_delay(payload, activity_name)
    workflow_id = activity.info().workflow_id
    request = PostInvoiceRequest(
        idempotency_key=_idempotency_key(workflow_id, activity_name),
        invoice_id=payload.invoice_id,
        company_id=payload.company_id,
        amount=payload.amount,
    )
    async with httpx.AsyncClient(base_url=EXTERNAL_SIM_URL) as client:
        response = await client.post("/erp/invoices", content=request.model_dump_json())
        response.raise_for_status()


@activity.defn
async def void_erp_post(payload: InvoiceDemoPayload) -> None:
    workflow_id = activity.info().workflow_id
    idempotency_key = _idempotency_key(workflow_id, "post_to_erp")
    async with httpx.AsyncClient(base_url=EXTERNAL_SIM_URL) as client:
        response = await client.delete(f"/erp/invoices/{idempotency_key}")
        response.raise_for_status()


@activity.defn
async def schedule_payment(payload: InvoiceDemoPayload) -> None:
    activity_name = "schedule_payment"
    _maybe_inject_failure(payload, activity_name)
    await _maybe_inject_delay(payload, activity_name)
    workflow_id = activity.info().workflow_id
    request = SchedulePaymentRequest(
        idempotency_key=_idempotency_key(workflow_id, activity_name),
        invoice_id=payload.invoice_id,
        amount=payload.amount,
    )
    async with httpx.AsyncClient(base_url=EXTERNAL_SIM_URL) as client:
        response = await client.post("/payments/schedule", content=request.model_dump_json())
        response.raise_for_status()


@activity.defn
async def confirm_payment(payload: InvoiceDemoPayload) -> None:
    activity_name = "confirm_payment"
    _maybe_inject_failure(payload, activity_name)
    await _maybe_inject_delay(payload, activity_name)
    workflow_id = activity.info().workflow_id
    request = ConfirmPaymentRequest(
        idempotency_key=_idempotency_key(workflow_id, activity_name),
        invoice_id=payload.invoice_id,
    )
    async with httpx.AsyncClient(base_url=EXTERNAL_SIM_URL) as client:
        response = await client.post("/payments/confirm", content=request.model_dump_json())
        response.raise_for_status()
