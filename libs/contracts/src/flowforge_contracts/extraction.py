from datetime import datetime

from pydantic import BaseModel

from flowforge_contracts.invoice_extraction import ExtractionRunMetadata, InvoiceExtraction


class RecordExtractionRequest(BaseModel):
    idempotency_key: str
    document_id: str
    company_id: str
    extraction: InvoiceExtraction
    run_metadata: ExtractionRunMetadata


class ExtractionResponse(BaseModel):
    idempotency_key: str
    document_id: str
    company_id: str
    extraction: InvoiceExtraction
    run_metadata: ExtractionRunMetadata
    created_at: datetime
