INVOICE_PAYLOAD = {
    "idempotency_key": "wf-1-post_to_erp",
    "invoice_id": "inv-1",
    "company_id": "company-1",
    "amount": {"amount": "100.00", "currency": "PEN"},
}


def test_post_invoice_creates_a_record(client):
    response = client.post("/erp/invoices", json=INVOICE_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"idempotency_key": "wf-1-post_to_erp", "status": "posted"}


def test_post_invoice_is_idempotent(client):
    client.post("/erp/invoices", json=INVOICE_PAYLOAD)
    client.post("/erp/invoices", json=INVOICE_PAYLOAD)
    assert len(client.app.state.store._erp_invoices) == 1


def test_void_invoice_marks_it_voided(client):
    client.post("/erp/invoices", json=INVOICE_PAYLOAD)
    response = client.delete(f"/erp/invoices/{INVOICE_PAYLOAD['idempotency_key']}")
    assert response.json() == {"idempotency_key": "wf-1-post_to_erp", "status": "voided"}


def test_void_of_unknown_invoice_returns_not_found_status(client):
    response = client.delete("/erp/invoices/unknown-key")
    assert response.json() == {"idempotency_key": "unknown-key", "status": "not_found"}
