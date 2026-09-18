from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.jurisdiction import Jurisdiction
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine
from jurisdiction_packs.pe.bank_account import validate_cci
from jurisdiction_packs.pe.tax_id import normalize_ruc, validate_ruc
from jurisdiction_packs.pe.ubl import generate_xml as generate_ubl_xml
from jurisdiction_packs.pe.ubl import parse_structured as parse_ubl_xml
from jurisdiction_packs.protocol import CreditNoteKind, ExchangeRateRule, RoundingPolicy, ValidationResult

IGV_RATE = Decimal("0.18")


class PeruJurisdictionPack:
    code: Jurisdiction = "PE"

    def normalize_tax_id(self, raw: str) -> str:
        return normalize_ruc(raw)

    def validate_tax_id(self, tax_id: str) -> ValidationResult:
        return validate_ruc(tax_id)

    def validate_bank_account(self, kind: str, value: str) -> ValidationResult:
        if kind != "CCI":
            return ValidationResult(is_valid=False, reason=f"unknown account kind {kind!r} for PE")
        return validate_cci(value)

    def parse_structured(self, xml: bytes) -> CanonicalInvoice | CanonicalCreditNote:
        return parse_ubl_xml(xml)

    def generate_xml(self, invoice: CanonicalInvoice) -> bytes:
        return generate_ubl_xml(invoice)

    def normalize_series_number(self, raw: str) -> str:
        return raw.strip().upper()

    def classify_credit_note(self, doc: CanonicalCreditNote) -> CreditNoteKind:
        return doc.scope

    def expected_taxes(self, invoice: CanonicalInvoice) -> list[TaxLine]:
        subtotal = sum((line.line_total.amount for line in invoice.lines), Decimal("0"))
        currency = invoice.payable.currency
        tax_amount = (subtotal * IGV_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return [
            TaxLine(
                tax_type="IGV", rate=IGV_RATE,
                base=Money(amount=subtotal, currency=currency),
                amount=Money(amount=tax_amount, currency=currency),
            )
        ]

    def withholdings(
        self, invoice: CanonicalInvoice, supplier: Any, company: Any
    ) -> list[WithholdingLine]:
        rate = getattr(supplier, "detraction_rate", None)
        if rate is None:
            return []
        currency = invoice.payable.currency
        amount = (invoice.payable.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return [
            WithholdingLine(
                kind="detraction", rate=rate, amount=Money(amount=amount, currency=currency), code="037"
            )
        ]

    def rounding(self) -> RoundingPolicy:
        return RoundingPolicy(decimal_places=2, rounding_mode="ROUND_HALF_UP")

    def exchange_rate_rule(self) -> ExchangeRateRule:
        return ExchangeRateRule(rate_source="datagen-simulated", as_of="issue_date")

    def payment_instructions(
        self, invoice: CanonicalInvoice, accounts: list[Any]
    ) -> list[dict[str, object]]:
        instructions: list[dict[str, object]] = [
            {"amount": w.amount, "account": None, "kind": w.kind} for w in invoice.withholdings
        ]
        instructions.append(
            {"amount": invoice.payable, "account": invoice.bank_account, "kind": "net_to_supplier"}
        )
        return instructions

    def extraction_glossary(self) -> str:
        return (
            "RUC: 11-digit Peruvian tax ID with a check digit. IGV: 18% general sales tax. "
            "Detraccion (SPOT): a percentage of the invoice deposited into a separate "
            "detraction account instead of paid directly to the supplier. "
            "CCI: 20-digit Peruvian interbank account number."
        )

    def equals(self, field: str, actual: Any, expected: Any) -> bool:
        if isinstance(actual, Decimal) and isinstance(expected, Decimal):
            return abs(actual - expected) < Decimal("0.01")
        return actual == expected
