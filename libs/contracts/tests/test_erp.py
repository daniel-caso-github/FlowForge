from decimal import Decimal

from flowforge_contracts.erp import (
    ConfirmPaymentRequest,
    PostInvoiceRequest,
    SchedulePaymentRequest,
)
from flowforge_contracts.money import Money


def test_post_invoice_request_round_trips_through_json():
    request = PostInvoiceRequest(
        idempotency_key="wf-1-post_to_erp",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )
    restored = PostInvoiceRequest.model_validate_json(request.model_dump_json())
    assert restored == request


def test_schedule_payment_request_holds_amount():
    request = SchedulePaymentRequest(
        idempotency_key="wf-1-schedule_payment",
        invoice_id="inv-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )
    assert request.amount.amount == Decimal("100.00")


def test_confirm_payment_request_holds_idempotency_key():
    request = ConfirmPaymentRequest(idempotency_key="wf-1-confirm_payment", invoice_id="inv-1")
    assert request.idempotency_key == "wf-1-confirm_payment"
