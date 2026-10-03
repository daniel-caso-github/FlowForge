from fastapi import APIRouter, Depends, HTTPException
from flowforge_contracts.extraction import ExtractionResponse, RecordExtractionRequest
from sqlalchemy.orm import Session

from invoice_service.api.mappers import to_extraction_response
from invoice_service.application.commands.record_extraction import (
    RecordExtractionCommand,
    RecordExtractionCommandHandler,
)
from invoice_service.application.queries.get_extraction import (
    GetExtractionQuery,
    GetExtractionQueryHandler,
)
from invoice_service.application.queries.list_extractions_by_document import (
    ListExtractionsByDocumentQuery,
    ListExtractionsByDocumentQueryHandler,
)
from invoice_service.domain.extraction import ExtractionRepository
from invoice_service.infrastructure.db import get_db
from invoice_service.infrastructure.repository import SqlAlchemyExtractionRepository

router = APIRouter()


def get_repository(db: Session = Depends(get_db)) -> ExtractionRepository:
    return SqlAlchemyExtractionRepository(db)


@router.post("/extractions", response_model=ExtractionResponse)
def record_extraction(
    request: RecordExtractionRequest,
    repository: ExtractionRepository = Depends(get_repository),
) -> ExtractionResponse:
    handler = RecordExtractionCommandHandler(repository)
    command = RecordExtractionCommand(
        idempotency_key=request.idempotency_key,
        document_id=request.document_id,
        company_id=request.company_id,
        extraction=request.extraction,
        run_metadata=request.run_metadata,
    )
    extraction = handler.handle(command)
    return to_extraction_response(extraction)


@router.get("/extractions/{idempotency_key}", response_model=ExtractionResponse)
def get_extraction(
    idempotency_key: str,
    repository: ExtractionRepository = Depends(get_repository),
) -> ExtractionResponse:
    handler = GetExtractionQueryHandler(repository)
    extraction = handler.handle(GetExtractionQuery(idempotency_key=idempotency_key))
    if extraction is None:
        raise HTTPException(status_code=404, detail="extraction not found")
    return to_extraction_response(extraction)


@router.get("/documents/{document_id}/extractions", response_model=list[ExtractionResponse])
def list_extractions_by_document(
    document_id: str,
    repository: ExtractionRepository = Depends(get_repository),
) -> list[ExtractionResponse]:
    handler = ListExtractionsByDocumentQueryHandler(repository)
    extractions = handler.handle(ListExtractionsByDocumentQuery(document_id=document_id))
    return [to_extraction_response(e) for e in extractions]
