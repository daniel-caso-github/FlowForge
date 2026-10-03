from dataclasses import dataclass

from invoice_service.domain.extraction import Extraction, ExtractionRepository


@dataclass
class ListExtractionsByDocumentQuery:
    document_id: str


class ListExtractionsByDocumentQueryHandler:
    def __init__(self, repository: ExtractionRepository) -> None:
        self._repository = repository

    def handle(self, query: ListExtractionsByDocumentQuery) -> list[Extraction]:
        return self._repository.list_by_document(query.document_id)
