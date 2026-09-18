from decimal import Decimal

import pytest
from budget_service.application.budget_service import (
    BudgetApplicationService,
    ReservationNotFoundError,
)
from budget_service.domain.reservation import BudgetReservation


class FakeBudgetReservationRepository:
    def __init__(self) -> None:
        self._reservations: dict[str, BudgetReservation] = {}

    def get(self, idempotency_key: str) -> BudgetReservation | None:
        return self._reservations.get(idempotency_key)

    def add(self, reservation: BudgetReservation) -> None:
        self._reservations[reservation.idempotency_key] = reservation

    def update(self, reservation: BudgetReservation) -> None:
        self._reservations[reservation.idempotency_key] = reservation


def test_reserve_creates_a_new_reservation():
    service = BudgetApplicationService(FakeBudgetReservationRepository())

    reservation = service.reserve(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    assert reservation.status == "reserved"
    assert reservation.idempotency_key == "wf-1-reserve_budget"


def test_reserve_is_idempotent_for_the_same_key():
    repository = FakeBudgetReservationRepository()
    service = BudgetApplicationService(repository)

    first = service.reserve(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    second = service.reserve(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    assert first == second
    assert len(repository._reservations) == 1


def test_release_marks_an_existing_reservation_released():
    repository = FakeBudgetReservationRepository()
    service = BudgetApplicationService(repository)
    service.reserve(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    reservation = service.release("wf-1-reserve_budget")

    assert reservation.status == "released"


def test_release_of_unknown_key_raises_reservation_not_found():
    service = BudgetApplicationService(FakeBudgetReservationRepository())

    with pytest.raises(ReservationNotFoundError):
        service.release("unknown-key")
