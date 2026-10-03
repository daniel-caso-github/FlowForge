def test_get_extraction_returns_the_stored_extraction(client, make_extraction_payload):
    client.post("/extractions", json=make_extraction_payload("doc-1-attempt-1"))

    response = client.get("/extractions/doc-1-attempt-1")

    assert response.status_code == 200
    assert response.json()["idempotency_key"] == "doc-1-attempt-1"


def test_get_extraction_returns_404_for_unknown_key(client):
    response = client.get("/extractions/missing")
    assert response.status_code == 404
