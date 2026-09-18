from sqlalchemy.orm import Session

from budget_service.domain.reservation import BudgetReservation
from budget_service.infrastructure.models import BudgetReservationModel


class SqlAlchemyBudgetReservationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, idempotency_key: str) -> BudgetReservation | None:
        record = self._session.get(BudgetReservationModel, idempotency_key)
        if record is None:
            return None
        return _to_domain(record)

    def add(self, reservation: BudgetReservation) -> None:
        record = BudgetReservationModel(
            idempotency_key=reservation.idempotency_key,
            invoice_id=reservation.invoice_id,
            company_id=reservation.company_id,
            amount=reservation.amount,
            currency=reservation.currency,
            status=reservation.status,
        )
        self._session.add(record)
        self._session.commit()

    def update(self, reservation: BudgetReservation) -> None:
        record = self._session.get(BudgetReservationModel, reservation.idempotency_key)
        assert record is not None, "update() requires an existing record"
        record.status = reservation.status
        self._session.commit()


def _to_domain(record: BudgetReservationModel) -> BudgetReservation:
    return BudgetReservation(
        idempotency_key=record.idempotency_key,
        invoice_id=record.invoice_id,
        company_id=record.company_id,
        amount=record.amount,
        currency=record.currency,
        status=record.status,
    )
