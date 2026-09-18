def test_release_marks_an_existing_reservation_released(client):
    reserve_payload = {
        "idempotency_key": "wf-1-reserve_budget",
        "invoice_id": "inv-1",
        "company_id": "company-1",
        "amount": {"amount": "100.00", "currency": "PEN"},
    }
    client.post("/reservations", json=reserve_payload)

    response = client.post("/reservations/wf-1-reserve_budget/release")
    assert response.status_code == 200
    assert response.json() == {"idempotency_key": "wf-1-reserve_budget", "status": "released"}


def test_release_is_idempotent(client):
    reserve_payload = {
        "idempotency_key": "wf-1-reserve_budget",
        "invoice_id": "inv-1",
        "company_id": "company-1",
        "amount": {"amount": "100.00", "currency": "PEN"},
    }
    client.post("/reservations", json=reserve_payload)
    first = client.post("/reservations/wf-1-reserve_budget/release")
    second = client.post("/reservations/wf-1-reserve_budget/release")
    assert first.json() == second.json()


def test_release_of_unknown_key_returns_404(client):
    response = client.post("/reservations/unknown-key/release")
    assert response.status_code == 404
