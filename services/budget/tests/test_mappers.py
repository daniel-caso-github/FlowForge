from decimal import Decimal

from budget_service.api.mappers import to_reserve_budget_response
from budget_service.domain.reservation import BudgetReservation


def test_to_reserve_budget_response_maps_key_and_status():
    reservation = BudgetReservation(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
        status="reserved",
    )

    response = to_reserve_budget_response(reservation)

    assert response.idempotency_key == "wf-1-reserve_budget"
    assert response.status == "reserved"
