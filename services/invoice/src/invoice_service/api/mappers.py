from datetime import UTC

from flowforge_contracts.extraction import ExtractionResponse

from invoice_service.domain.extraction import Extraction


def to_extraction_response(extraction: Extraction) -> ExtractionResponse:
    created_at = extraction.created_at
    if created_at.tzinfo is None:
        # SQLite's DateTime(timezone=True) round-trips as naive; every
        # created_at written by this service is UTC (see RecordExtractionCommandHandler).
        created_at = created_at.replace(tzinfo=UTC)

    # SQLite's generic Numeric column pads cost_usd with trailing zeros on
    # round-trip (e.g. 0.001 -> 0.0010000000); normalize restores the original
    # representation. Decimal equality ignores trailing zeros, so this must run
    # unconditionally rather than behind a `!=` check.
    run_metadata = extraction.run_metadata.model_copy(
        update={"cost_usd": extraction.run_metadata.cost_usd.normalize()}
    )

    return ExtractionResponse(
        idempotency_key=extraction.idempotency_key,
        document_id=extraction.document_id,
        company_id=extraction.company_id,
        extraction=extraction.extraction,
        run_metadata=run_metadata,
        created_at=created_at,
    )
