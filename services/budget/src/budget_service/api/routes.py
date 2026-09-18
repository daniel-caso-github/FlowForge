from fastapi import APIRouter, Depends, HTTPException
from flowforge_contracts.budget import ReserveBudgetRequest, ReserveBudgetResponse
from sqlalchemy.orm import Session

from budget_service.api.mappers import to_reserve_budget_response
from budget_service.application.budget_service import (
    BudgetApplicationService,
    ReservationNotFoundError,
)
from budget_service.infrastructure.db import get_db
from budget_service.infrastructure.repository import SqlAlchemyBudgetReservationRepository

router = APIRouter()


def get_budget_service(db: Session = Depends(get_db)) -> BudgetApplicationService:
    return BudgetApplicationService(SqlAlchemyBudgetReservationRepository(db))


@router.post("/reservations", response_model=ReserveBudgetResponse)
def reserve(
    request: ReserveBudgetRequest,
    service: BudgetApplicationService = Depends(get_budget_service),
) -> ReserveBudgetResponse:
    reservation = service.reserve(
        idempotency_key=request.idempotency_key,
        invoice_id=request.invoice_id,
        company_id=request.company_id,
        amount=request.amount.amount,
        currency=request.amount.currency,
    )
    return to_reserve_budget_response(reservation)


@router.post("/reservations/{idempotency_key}/release", response_model=ReserveBudgetResponse)
def release(
    idempotency_key: str,
    service: BudgetApplicationService = Depends(get_budget_service),
) -> ReserveBudgetResponse:
    try:
        reservation = service.release(idempotency_key)
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="reservation not found") from exc
    return to_reserve_budget_response(reservation)
