from typing import Literal

from pydantic import BaseModel

Confidence = Literal["high", "medium", "low"]


class ExtractedField[T](BaseModel):
    value: T | None
    evidence: str | None
    page: int | None
    confidence: Confidence
    signals: list[str]
