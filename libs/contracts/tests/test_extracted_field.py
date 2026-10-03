from flowforge_contracts.extracted_field import ExtractedField


def test_extracted_field_holds_value_evidence_and_confidence():
    field = ExtractedField[str](
        value="20123456789",
        evidence="RUC: 20123456789",
        page=1,
        confidence="high",
        signals=["checksum_ok"],
    )
    assert field.value == "20123456789"
    assert field.confidence == "high"
    assert field.signals == ["checksum_ok"]


def test_extracted_field_allows_missing_value():
    field = ExtractedField[str](
        value=None, evidence=None, page=None, confidence="low", signals=[]
    )
    assert field.value is None
