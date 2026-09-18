from decimal import Decimal

from budget_service.application.commands.reserve_budget import (
    ReserveBudgetCommand,
    ReserveBudgetCommandHandler,
)


def test_reserve_creates_a_new_reservation(fake_repository):
    handler = ReserveBudgetCommandHandler(fake_repository)

    reservation = handler.handle(
        ReserveBudgetCommand(
            idempotency_key="wf-1-reserve_budget",
            invoice_id="inv-1",
            company_id="company-1",
            amount=Decimal("100.00"),
            currency="PEN",
        )
    )

    assert reservation.status == "reserved"
    assert reservation.idempotency_key == "wf-1-reserve_budget"


def test_reserve_is_idempotent_for_the_same_key(fake_repository):
    handler = ReserveBudgetCommandHandler(fake_repository)
    command = ReserveBudgetCommand(
        idempotency_key="wf-1-reserve_budget",
        invoice_id="inv-1",
        company_id="company-1",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    first = handler.handle(command)
    second = handler.handle(command)

    assert first == second
    assert len(fake_repository.reservations) == 1
