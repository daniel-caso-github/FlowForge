def test_list_extractions_returns_all_versions_for_a_document(client, make_extraction_payload):
    client.post("/extractions", json=make_extraction_payload("doc-1-attempt-1", "doc-1"))
    client.post("/extractions", json=make_extraction_payload("doc-1-attempt-2", "doc-1"))
    client.post("/extractions", json=make_extraction_payload("doc-2-attempt-1", "doc-2"))

    response = client.get("/documents/doc-1/extractions")

    assert response.status_code == 200
    keys = {item["idempotency_key"] for item in response.json()}
    assert keys == {"doc-1-attempt-1", "doc-1-attempt-2"}
