from budget_service.main import app
from budget_service.models import BudgetReservation
from budget_service.routes import get_db
from sqlalchemy import select


def test_reserve_creates_a_reservation(client):
    response = client.post(
        "/reservations",
        json={
            "idempotency_key": "wf-1-reserve_budget",
            "invoice_id": "inv-1",
            "company_id": "company-1",
            "amount": {"amount": "100.00", "currency": "PEN"},
        },
    )
    assert response.status_code == 200
    assert response.json() == {"idempotency_key": "wf-1-reserve_budget", "status": "reserved"}


def test_reserve_is_idempotent_for_the_same_key(client):
    payload = {
        "idempotency_key": "wf-1-reserve_budget",
        "invoice_id": "inv-1",
        "company_id": "company-1",
        "amount": {"amount": "100.00", "currency": "PEN"},
    }
    first = client.post("/reservations", json=payload)
    second = client.post("/reservations", json=payload)
    assert first.json() == second.json()

    override = app.dependency_overrides[get_db]
    db = next(override())
    rows = db.execute(select(BudgetReservation)).scalars().all()
    assert len(rows) == 1
