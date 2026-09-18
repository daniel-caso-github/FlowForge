from decimal import Decimal

from budget_service.domain.reservation import BudgetReservation, BudgetReservationRepository


class ReservationNotFoundError(Exception):
    pass


class BudgetApplicationService:
    def __init__(self, repository: BudgetReservationRepository) -> None:
        self._repository = repository

    def reserve(
        self,
        idempotency_key: str,
        invoice_id: str,
        company_id: str,
        amount: Decimal,
        currency: str,
    ) -> BudgetReservation:
        existing = self._repository.get(idempotency_key)
        if existing is not None:
            return existing

        reservation = BudgetReservation(
            idempotency_key=idempotency_key,
            invoice_id=invoice_id,
            company_id=company_id,
            amount=amount,
            currency=currency,
            status="reserved",
        )
        self._repository.add(reservation)
        return reservation

    def release(self, idempotency_key: str) -> BudgetReservation:
        reservation = self._repository.get(idempotency_key)
        if reservation is None:
            raise ReservationNotFoundError(idempotency_key)
        reservation.status = "released"
        self._repository.update(reservation)
        return reservation
