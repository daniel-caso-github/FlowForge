from decimal import Decimal

from flowforge_contracts.budget import (
    ReleaseBudgetRequest,
    ReserveBudgetRequest,
    ReserveBudgetResponse,
)
from flowforge_contracts.money import Money


def test_reserve_budget_request_round_trips_through_json():
    request = ReserveBudgetRequest(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )
    restored = ReserveBudgetRequest.model_validate_json(request.model_dump_json())
    assert restored == request


def test_reserve_budget_response_holds_status():
    response = ReserveBudgetResponse(idempotency_key="wf-1-reserve_budget", status="reserved")
    assert response.status == "reserved"


def test_release_budget_request_holds_idempotency_key():
    request = ReleaseBudgetRequest(idempotency_key="wf-1-reserve_budget")
    assert request.idempotency_key == "wf-1-reserve_budget"
