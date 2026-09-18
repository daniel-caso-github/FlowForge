from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.money import Money


def _converted(amount: Decimal, currency: str, rate_date: date) -> ConvertedMoney:
    money = Money(amount=amount, currency=currency)
    return ConvertedMoney(
        original=money, base=money, rate=Decimal("1"), rate_date=rate_date,
        rate_source="datagen-simulated",
    )


def inject_wrong_tax_calculation(invoice: CanonicalInvoice) -> CanonicalInvoice:
    wrong_amount = invoice.taxes[0].amount.amount + Decimal("5.00")
    wrong_tax = invoice.taxes[0].model_copy(
        update={"amount": Money(amount=wrong_amount, currency=invoice.taxes[0].amount.currency)}
    )
    subtotal = invoice.subtotal.original.amount
    withholding_total = sum((w.amount.amount for w in invoice.withholdings), Decimal("0"))
    new_total = subtotal + wrong_amount
    return invoice.model_copy(update={
        "taxes": [wrong_tax],
        "total": _converted(new_total, invoice.total.original.currency, invoice.total.rate_date),
        "payable": Money(amount=new_total - withholding_total, currency=invoice.payable.currency),
    })


def inject_missing_withholding(invoice: CanonicalInvoice) -> CanonicalInvoice:
    return invoice.model_copy(update={
        "withholdings": [],
        "payable": Money(amount=invoice.total.original.amount, currency=invoice.payable.currency),
    })


def inject_invalid_tax_id(invoice: CanonicalInvoice) -> CanonicalInvoice:
    tax_id = invoice.supplier_tax_id
    replacement = "0" if tax_id[-1] != "0" else "1"
    return invoice.model_copy(update={"supplier_tax_id": tax_id[:-1] + replacement})


def inject_multi_currency(
    invoice: CanonicalInvoice, rate: Decimal, foreign_currency: str
) -> CanonicalInvoice:
    def _convert(cm: ConvertedMoney) -> ConvertedMoney:
        base_amount = (cm.original.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cm.model_copy(update={
            "original": Money(amount=cm.original.amount, currency=foreign_currency),
            "base": Money(amount=base_amount, currency=cm.base.currency),
            "rate": rate,
        })

    return invoice.model_copy(
        update={"subtotal": _convert(invoice.subtotal), "total": _convert(invoice.total)}
    )


def build_credit_note(
    invoice: CanonicalInvoice, scope: Literal["full", "partial"]
) -> CanonicalCreditNote:
    lines = invoice.lines if scope == "full" else invoice.lines[: max(1, len(invoice.lines) // 2)]
    total_amount = sum((line.line_total.amount for line in lines), Decimal("0"))
    es_mode = "differences" if invoice.jurisdiction == "ES" and scope == "partial" else None
    return CanonicalCreditNote(
        credit_note_key=f"{invoice.invoice_key}:CN",
        references_invoice_key=invoice.invoice_key,
        scope=scope, reason_code="01", es_rectification_mode=es_mode, lines=lines,
        total=_converted(total_amount, invoice.total.original.currency, invoice.total.rate_date),
    )


def build_duplicate_pair(invoice: CanonicalInvoice) -> tuple[CanonicalInvoice, CanonicalInvoice]:
    duplicate = invoice.model_copy(update={
        "invoice_key": invoice.invoice_key + "-DUP",
        "series_number": invoice.series_number + "-DUP",
    })
    return invoice, duplicate
