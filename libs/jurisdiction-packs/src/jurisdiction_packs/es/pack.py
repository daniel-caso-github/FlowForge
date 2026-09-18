from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.jurisdiction import Jurisdiction
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine
from jurisdiction_packs.es.bank_account import validate_iban
from jurisdiction_packs.es.facturae import generate_xml as generate_facturae_xml
from jurisdiction_packs.es.facturae import parse_structured as parse_facturae_xml
from jurisdiction_packs.es.tax_id import validate_cif, validate_nif
from jurisdiction_packs.protocol import CreditNoteKind, ExchangeRateRule, RoundingPolicy, ValidationResult

IVA_RATE = Decimal("21.00")


class SpainJurisdictionPack:
    code: Jurisdiction = "ES"

    def normalize_tax_id(self, raw: str) -> str:
        return raw.strip().upper()

    def validate_tax_id(self, tax_id: str) -> ValidationResult:
        tax_id = self.normalize_tax_id(tax_id)
        if len(tax_id) == 9 and tax_id[0].isalpha() and tax_id[1:8].isdigit():
            return validate_cif(tax_id)
        if len(tax_id) == 9 and tax_id[:8].isdigit() and tax_id[8].isalpha():
            return validate_nif(tax_id)
        return ValidationResult(is_valid=False, reason="not a recognizable NIF or CIF shape")

    def validate_bank_account(self, kind: str, value: str) -> ValidationResult:
        if kind != "IBAN":
            return ValidationResult(is_valid=False, reason=f"unknown account kind {kind!r} for ES")
        return validate_iban(value)

    def parse_structured(self, xml: bytes) -> CanonicalInvoice | CanonicalCreditNote:
        return parse_facturae_xml(xml)

    def generate_xml(self, invoice: CanonicalInvoice) -> bytes:
        return generate_facturae_xml(invoice)

    def normalize_series_number(self, raw: str) -> str:
        return raw.strip().upper()

    def classify_credit_note(self, doc: CanonicalCreditNote) -> CreditNoteKind:
        return doc.scope

    def expected_taxes(self, invoice: CanonicalInvoice) -> list[TaxLine]:
        subtotal = sum((line.line_total.amount for line in invoice.lines), Decimal("0"))
        currency = invoice.payable.currency
        rate_fraction = IVA_RATE / Decimal("100")
        tax_amount = (subtotal * rate_fraction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return [
            TaxLine(
                tax_type="IVA", rate=IVA_RATE,
                base=Money(amount=subtotal, currency=currency),
                amount=Money(amount=tax_amount, currency=currency),
            )
        ]

    def withholdings(
        self, invoice: CanonicalInvoice, supplier: Any, company: Any
    ) -> list[WithholdingLine]:
        if not getattr(supplier, "subject_to_irpf", False):
            return []
        rate = supplier.irpf_rate
        currency = invoice.payable.currency
        amount = (invoice.payable.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return [
            WithholdingLine(kind="irpf", rate=rate, amount=Money(amount=amount, currency=currency), code=None)
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
            "NIF/CIF: Spanish tax ID (individuals: 8 digits + control letter; entities: "
            "a letter + 7 digits + control character). IVA: value-added tax, 21% general "
            "rate. IRPF withholding: personal income tax withheld on certain professional "
            "services invoices. IBAN: 24-character Spanish bank account identifier."
        )

    def equals(self, field: str, actual: Any, expected: Any) -> bool:
        if isinstance(actual, Decimal) and isinstance(expected, Decimal):
            return abs(actual - expected) < Decimal("0.01")
        return actual == expected
