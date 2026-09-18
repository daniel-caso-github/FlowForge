from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.jurisdiction import Jurisdiction
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine


class CanonicalInvoice(BaseModel):
    invoice_key: str
    company_id: UUID
    jurisdiction: Jurisdiction
    supplier_tax_id: str
    series_number: str
    issue_date: date
    due_date: date | None = None
    po_reference: str | None = None
    lines: list[InvoiceLine]
    subtotal: ConvertedMoney
    taxes: list[TaxLine]
    withholdings: list[WithholdingLine]
    total: ConvertedMoney
    payable: Money
    bank_account: BankAccountRef
    source_extraction_id: UUID


class CanonicalCreditNote(BaseModel):
    credit_note_key: str
    references_invoice_key: str
    scope: Literal["full", "partial"]
    reason_code: str
    es_rectification_mode: Literal["differences", "substitution"] | None = None
    lines: list[InvoiceLine]
    total: ConvertedMoney
