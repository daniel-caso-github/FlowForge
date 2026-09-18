from fastapi import APIRouter, Depends, HTTPException
from flowforge_contracts.budget import ReserveBudgetRequest, ReserveBudgetResponse
from sqlalchemy.orm import Session

from budget_service.db import SessionLocal
from budget_service.models import BudgetReservation

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/reservations", response_model=ReserveBudgetResponse)
def reserve(
    request: ReserveBudgetRequest, db: Session = Depends(get_db)
) -> ReserveBudgetResponse:
    existing = db.get(BudgetReservation, request.idempotency_key)
    if existing is not None:
        return ReserveBudgetResponse(idempotency_key=existing.idempotency_key, status=existing.status)

    reservation = BudgetReservation(
        idempotency_key=request.idempotency_key,
        invoice_id=request.invoice_id,
        company_id=request.company_id,
        amount=request.amount.amount,
        currency=request.amount.currency,
        status="reserved",
    )
    db.add(reservation)
    db.commit()
    return ReserveBudgetResponse(idempotency_key=reservation.idempotency_key, status=reservation.status)


@router.post("/reservations/{idempotency_key}/release", response_model=ReserveBudgetResponse)
def release(idempotency_key: str, db: Session = Depends(get_db)) -> ReserveBudgetResponse:
    reservation = db.get(BudgetReservation, idempotency_key)
    if reservation is None:
        raise HTTPException(status_code=404, detail="reservation not found")
    reservation.status = "released"
    db.commit()
    return ReserveBudgetResponse(idempotency_key=reservation.idempotency_key, status=reservation.status)
