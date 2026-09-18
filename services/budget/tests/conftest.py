import pytest
from budget_service.domain.reservation import BudgetReservation
from budget_service.infrastructure.db import Base, get_db
from budget_service.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class FakeBudgetReservationRepository:
    def __init__(self) -> None:
        self.reservations: dict[str, BudgetReservation] = {}

    def get(self, idempotency_key: str) -> BudgetReservation | None:
        return self.reservations.get(idempotency_key)

    def add(self, reservation: BudgetReservation) -> None:
        self.reservations[reservation.idempotency_key] = reservation

    def update(self, reservation: BudgetReservation) -> None:
        self.reservations[reservation.idempotency_key] = reservation


@pytest.fixture()
def fake_repository() -> FakeBudgetReservationRepository:
    return FakeBudgetReservationRepository()


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
