SCHEDULE_PAYLOAD = {
    "idempotency_key": "wf-1-schedule_payment",
    "invoice_id": "inv-1",
    "amount": {"amount": "100.00", "currency": "PEN"},
}
CONFIRM_PAYLOAD = {"idempotency_key": "wf-1-confirm_payment", "invoice_id": "inv-1"}


def test_schedule_payment_creates_a_record(client):
    response = client.post("/payments/schedule", json=SCHEDULE_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"idempotency_key": "wf-1-schedule_payment", "status": "scheduled"}


def test_schedule_payment_is_idempotent(client):
    client.post("/payments/schedule", json=SCHEDULE_PAYLOAD)
    client.post("/payments/schedule", json=SCHEDULE_PAYLOAD)
    assert len(client.app.state.store._payments) == 1


def test_confirm_payment_marks_it_confirmed(client):
    schedule_for_confirm = {**SCHEDULE_PAYLOAD, "idempotency_key": "wf-1-confirm_payment"}
    client.post("/payments/schedule", json=schedule_for_confirm)
    response = client.post("/payments/confirm", json=CONFIRM_PAYLOAD)
    assert response.json() == {"idempotency_key": "wf-1-confirm_payment", "status": "confirmed"}
