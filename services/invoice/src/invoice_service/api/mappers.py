from flowforge_contracts.extraction import ExtractionResponse

from invoice_service.domain.extraction import Extraction


def to_extraction_response(extraction: Extraction) -> ExtractionResponse:
    return ExtractionResponse(
        idempotency_key=extraction.idempotency_key,
        document_id=extraction.document_id,
        company_id=extraction.company_id,
        extraction=extraction.extraction,
        run_metadata=extraction.run_metadata,
        created_at=extraction.created_at,
    )
