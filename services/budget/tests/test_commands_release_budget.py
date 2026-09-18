from decimal import Decimal

import pytest
from budget_service.application.commands.release_budget import (
    ReleaseBudgetCommand,
    ReleaseBudgetCommandHandler,
)
from budget_service.application.commands.reserve_budget import (
    ReserveBudgetCommand,
    ReserveBudgetCommandHandler,
)
from budget_service.domain.reservation import ReservationNotFoundError


def test_release_marks_an_existing_reservation_released(fake_repository):
    ReserveBudgetCommandHandler(fake_repository).handle(
        ReserveBudgetCommand(
            idempotency_key="wf-1-reserve_budget",
            invoice_id="inv-1",
            company_id="company-1",
            amount=Decimal("100.00"),
            currency="PEN",
        )
    )

    reservation = ReleaseBudgetCommandHandler(fake_repository).handle(
        ReleaseBudgetCommand(idempotency_key="wf-1-reserve_budget")
    )

    assert reservation.status == "released"


def test_release_of_unknown_key_raises_reservation_not_found(fake_repository):
    handler = ReleaseBudgetCommandHandler(fake_repository)

    with pytest.raises(ReservationNotFoundError):
        handler.handle(ReleaseBudgetCommand(idempotency_key="unknown-key"))
