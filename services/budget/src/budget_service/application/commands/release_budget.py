from dataclasses import dataclass

from budget_service.domain.reservation import (
    BudgetReservation,
    BudgetReservationRepository,
    ReservationNotFoundError,
)


@dataclass
class ReleaseBudgetCommand:
    idempotency_key: str


class ReleaseBudgetCommandHandler:
    def __init__(self, repository: BudgetReservationRepository) -> None:
        self._repository = repository

    def handle(self, command: ReleaseBudgetCommand) -> BudgetReservation:
        reservation = self._repository.get(command.idempotency_key)
        if reservation is None:
            raise ReservationNotFoundError(command.idempotency_key)
        reservation.status = "released"
        self._repository.update(reservation)
        return reservation
