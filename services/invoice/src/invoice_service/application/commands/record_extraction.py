from dataclasses import dataclass
from datetime import UTC, datetime

from flowforge_contracts.invoice_extraction import ExtractionRunMetadata, InvoiceExtraction

from invoice_service.domain.extraction import Extraction, ExtractionRepository


@dataclass
class RecordExtractionCommand:
    idempotency_key: str
    document_id: str
    company_id: str
    extraction: InvoiceExtraction
    run_metadata: ExtractionRunMetadata


class RecordExtractionCommandHandler:
    def __init__(self, repository: ExtractionRepository) -> None:
        self._repository = repository

    def handle(self, command: RecordExtractionCommand) -> Extraction:
        existing = self._repository.get(command.idempotency_key)
        if existing is not None:
            return existing

        extraction = Extraction(
            idempotency_key=command.idempotency_key,
            document_id=command.document_id,
            company_id=command.company_id,
            extraction=command.extraction,
            run_metadata=command.run_metadata,
            created_at=datetime.now(UTC),
        )
        self._repository.add(extraction)
        return extraction
