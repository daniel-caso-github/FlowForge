from fastapi import APIRouter, Depends, HTTPException
from flowforge_contracts.budget import ReserveBudgetRequest, ReserveBudgetResponse
from sqlalchemy.orm import Session

from budget_service.api.mappers import to_reserve_budget_response
from budget_service.application.commands.release_budget import (
    ReleaseBudgetCommand,
    ReleaseBudgetCommandHandler,
)
from budget_service.application.commands.reserve_budget import (
    ReserveBudgetCommand,
    ReserveBudgetCommandHandler,
)
from budget_service.domain.reservation import BudgetReservationRepository, ReservationNotFoundError
from budget_service.infrastructure.db import get_db
from budget_service.infrastructure.repository import SqlAlchemyBudgetReservationRepository

router = APIRouter()


def get_repository(db: Session = Depends(get_db)) -> BudgetReservationRepository:
    return SqlAlchemyBudgetReservationRepository(db)


@router.post("/reservations", response_model=ReserveBudgetResponse)
def reserve(
    request: ReserveBudgetRequest,
    repository: BudgetReservationRepository = Depends(get_repository),
) -> ReserveBudgetResponse:
    handler = ReserveBudgetCommandHandler(repository)
    command = ReserveBudgetCommand(
        idempotency_key=request.idempotency_key,
        invoice_id=request.invoice_id,
        company_id=request.company_id,
        amount=request.amount.amount,
        currency=request.amount.currency,
    )
    reservation = handler.handle(command)
    return to_reserve_budget_response(reservation)


@router.post("/reservations/{idempotency_key}/release", response_model=ReserveBudgetResponse)
def release(
    idempotency_key: str,
    repository: BudgetReservationRepository = Depends(get_repository),
) -> ReserveBudgetResponse:
    handler = ReleaseBudgetCommandHandler(repository)
    try:
        reservation = handler.handle(ReleaseBudgetCommand(idempotency_key=idempotency_key))
    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="reservation not found") from exc
    return to_reserve_budget_response(reservation)
