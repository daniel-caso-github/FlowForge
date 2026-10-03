from decimal import Decimal

from pydantic import BaseModel

from flowforge_contracts.extracted_field import ExtractedField
from flowforge_contracts.money import Money


class InvoiceLineExtraction(BaseModel):
    line_number: int
    description: ExtractedField[str]
    quantity: ExtractedField[Decimal]
    unit_price: ExtractedField[Money]
    line_total: ExtractedField[Money]


class TaxLineExtraction(BaseModel):
    tax_type: ExtractedField[str]
    rate: ExtractedField[Decimal]
    base: ExtractedField[Money]
    amount: ExtractedField[Money]


class WithholdingLineExtraction(BaseModel):
    kind: ExtractedField[str]
    rate: ExtractedField[Decimal]
    amount: ExtractedField[Money]
    code: ExtractedField[str]


class BankAccountRefExtraction(BaseModel):
    account_number: ExtractedField[str]


class InvoiceExtraction(BaseModel):
    supplier_tax_id: ExtractedField[str]
    series_number: ExtractedField[str]
    issue_date: ExtractedField[str]
    due_date: ExtractedField[str]
    po_reference: ExtractedField[str]
    lines: list[InvoiceLineExtraction]
    subtotal: ExtractedField[Money]
    taxes: list[TaxLineExtraction]
    withholdings: list[WithholdingLineExtraction]
    total: ExtractedField[Money]
    bank_account: BankAccountRefExtraction


class ExtractionRunMetadata(BaseModel):
    base_model: str
    escalated: bool
    escalation_model: str | None
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    latency_ms: int
