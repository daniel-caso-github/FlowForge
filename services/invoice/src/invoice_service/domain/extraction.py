from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from flowforge_contracts.invoice_extraction import ExtractionRunMetadata, InvoiceExtraction


@dataclass
class Extraction:
    idempotency_key: str
    document_id: str
    company_id: str
    extraction: InvoiceExtraction
    run_metadata: ExtractionRunMetadata
    created_at: datetime


class ExtractionRepository(Protocol):
    def get(self, idempotency_key: str) -> Extraction | None: ...

    def list_by_document(self, document_id: str) -> list[Extraction]: ...

    def add(self, extraction: Extraction) -> None: ...
