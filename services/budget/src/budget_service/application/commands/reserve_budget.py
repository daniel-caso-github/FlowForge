from dataclasses import dataclass
from decimal import Decimal

from budget_service.domain.reservation import BudgetReservation, BudgetReservationRepository


@dataclass
class ReserveBudgetCommand:
    idempotency_key: str
    invoice_id: str
    company_id: str
    amount: Decimal
    currency: str


class ReserveBudgetCommandHandler:
    def __init__(self, repository: BudgetReservationRepository) -> None:
        self._repository = repository

    def handle(self, command: ReserveBudgetCommand) -> BudgetReservation:
        existing = self._repository.get(command.idempotency_key)
        if existing is not None:
            return existing

        reservation = BudgetReservation(
            idempotency_key=command.idempotency_key,
            invoice_id=command.invoice_id,
            company_id=command.company_id,
            amount=command.amount,
            currency=command.currency,
            status="reserved",
        )
        self._repository.add(reservation)
        return reservation
