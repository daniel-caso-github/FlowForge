from flowforge_contracts.invoice_extraction import ExtractionRunMetadata, InvoiceExtraction
from sqlalchemy import select
from sqlalchemy.orm import Session

from invoice_service.domain.extraction import Extraction
from invoice_service.infrastructure.models import ExtractionModel


class SqlAlchemyExtractionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, idempotency_key: str) -> Extraction | None:
        record = self._session.get(ExtractionModel, idempotency_key)
        if record is None:
            return None
        return _to_domain(record)

    def list_by_document(self, document_id: str) -> list[Extraction]:
        records = (
            self._session.execute(
                select(ExtractionModel)
                .where(ExtractionModel.document_id == document_id)
                .order_by(ExtractionModel.created_at)
            )
            .scalars()
            .all()
        )
        return [_to_domain(record) for record in records]

    def add(self, extraction: Extraction) -> None:
        record = ExtractionModel(
            idempotency_key=extraction.idempotency_key,
            document_id=extraction.document_id,
            company_id=extraction.company_id,
            extraction=extraction.extraction.model_dump(mode="json"),
            base_model=extraction.run_metadata.base_model,
            escalated=extraction.run_metadata.escalated,
            escalation_model=extraction.run_metadata.escalation_model,
            input_tokens=extraction.run_metadata.input_tokens,
            output_tokens=extraction.run_metadata.output_tokens,
            cost_usd=extraction.run_metadata.cost_usd,
            latency_ms=extraction.run_metadata.latency_ms,
            created_at=extraction.created_at,
        )
        self._session.add(record)
        self._session.commit()


def _to_domain(record: ExtractionModel) -> Extraction:
    return Extraction(
        idempotency_key=record.idempotency_key,
        document_id=record.document_id,
        company_id=record.company_id,
        extraction=InvoiceExtraction.model_validate(record.extraction),
        run_metadata=ExtractionRunMetadata(
            base_model=record.base_model,
            escalated=record.escalated,
            escalation_model=record.escalation_model,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            cost_usd=record.cost_usd,
            latency_ms=record.latency_ms,
        ),
        created_at=record.created_at,
    )
