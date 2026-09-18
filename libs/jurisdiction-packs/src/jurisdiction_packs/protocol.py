from typing import Any, Literal, Protocol

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.jurisdiction import Jurisdiction
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine
from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    reason: str | None = None


class RoundingPolicy(BaseModel):
    decimal_places: int
    rounding_mode: str


class ExchangeRateRule(BaseModel):
    rate_source: str
    as_of: Literal["issue_date"]


CreditNoteKind = Literal["full", "partial"]


class JurisdictionPack(Protocol):
    code: Jurisdiction

    def normalize_tax_id(self, raw: str) -> str: ...
    def validate_tax_id(self, tax_id: str) -> ValidationResult: ...
    def validate_bank_account(self, kind: str, value: str) -> ValidationResult: ...

    def parse_structured(self, xml: bytes) -> CanonicalInvoice | CanonicalCreditNote: ...
    def normalize_series_number(self, raw: str) -> str: ...
    def classify_credit_note(self, doc: CanonicalCreditNote) -> CreditNoteKind: ...

    def expected_taxes(self, invoice: CanonicalInvoice) -> list[TaxLine]: ...
    def withholdings(
        self, invoice: CanonicalInvoice, supplier: Any, company: Any
    ) -> list[WithholdingLine]: ...
    def rounding(self) -> RoundingPolicy: ...
    def exchange_rate_rule(self) -> ExchangeRateRule: ...

    def payment_instructions(
        self, invoice: CanonicalInvoice, accounts: list[Any]
    ) -> list[dict[str, object]]: ...
    def extraction_glossary(self) -> str: ...
    def equals(self, field: str, actual: Any, expected: Any) -> bool: ...
