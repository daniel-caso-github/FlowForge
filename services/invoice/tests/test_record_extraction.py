from invoice_service.infrastructure.db import get_db
from invoice_service.infrastructure.models import ExtractionModel
from invoice_service.main import app
from sqlalchemy import select


def test_record_extraction_creates_an_extraction(client, make_extraction_payload):
    response = client.post("/extractions", json=make_extraction_payload("doc-1-attempt-1"))

    assert response.status_code == 200
    body = response.json()
    assert body["idempotency_key"] == "doc-1-attempt-1"
    assert body["extraction"]["supplier_tax_id"]["value"] == "81618495930"


def test_record_extraction_is_idempotent_for_the_same_key(client, make_extraction_payload):
    payload = make_extraction_payload("doc-1-attempt-1")
    first = client.post("/extractions", json=payload)
    second = client.post("/extractions", json=payload)

    assert first.json() == second.json()

    override = app.dependency_overrides[get_db]
    db = next(override())
    rows = db.execute(select(ExtractionModel)).scalars().all()
    assert len(rows) == 1
