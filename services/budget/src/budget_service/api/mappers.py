from flowforge_contracts.budget import ReserveBudgetResponse

from budget_service.domain.reservation import BudgetReservation


def to_reserve_budget_response(reservation: BudgetReservation) -> ReserveBudgetResponse:
    return ReserveBudgetResponse(
        idempotency_key=reservation.idempotency_key, status=reservation.status
    )
