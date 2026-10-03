from dataclasses import dataclass

from invoice_service.domain.extraction import Extraction, ExtractionRepository


@dataclass
class GetExtractionQuery:
    idempotency_key: str


class GetExtractionQueryHandler:
    def __init__(self, repository: ExtractionRepository) -> None:
        self._repository = repository

    def handle(self, query: GetExtractionQuery) -> Extraction | None:
        return self._repository.get(query.idempotency_key)
