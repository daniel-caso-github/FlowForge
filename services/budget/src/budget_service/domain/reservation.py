from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass
class BudgetReservation:
    idempotency_key: str
    invoice_id: str
    company_id: str
    amount: Decimal
    currency: str
    status: str


class BudgetReservationRepository(Protocol):
    def get(self, idempotency_key: str) -> BudgetReservation | None: ...

    def add(self, reservation: BudgetReservation) -> None: ...

    def update(self, reservation: BudgetReservation) -> None: ...
