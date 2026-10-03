from decimal import Decimal
from io import BytesIO

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.money import Money
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LABELS: dict[str, dict[str, str]] = {
    "PE": {"tax_id_label": "RUC"},
    "ES": {"tax_id_label": "NIF/CIF"},
}

_LINE_HEADER = ["#", "Description", "Qty", "Unit price", "Line total"]


def _invariant_canvas(*args, **kwargs) -> Canvas:
    kwargs['invariant'] = 1
    return Canvas(*args, **kwargs)


def _build_pdf(elements: list) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(elements, canvasmaker=_invariant_canvas)
    return buffer.getvalue()


def _percent(rate: Decimal) -> Decimal:
    return rate if rate > 1 else rate * 100


def _money(money: Money) -> str:
    return f"{money.currency} {money.amount:.2f}"


def _converted_money(cm: ConvertedMoney) -> str:
    original = _money(cm.original)
    if cm.original.currency == cm.base.currency:
        return original
    return f"{original} ({_money(cm.base)} @ {cm.rate})"


def _line_items_table(lines) -> Table:
    rows = [_LINE_HEADER]
    for line in lines:
        rows.append([
            str(line.line_number), line.description, str(line.quantity),
            _money(line.unit_price), _money(line.line_total),
        ])
    return Table(rows, style=TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))


def render_invoice_pdf(
    invoice: CanonicalInvoice, supplier_name: str, company_name: str, company_tax_id: str,
) -> bytes:
    labels = LABELS[invoice.jurisdiction]
    styles = getSampleStyleSheet()

    elements = [
        Paragraph(f"INVOICE {invoice.series_number}", styles["Title"]),
        Spacer(1, 6 * mm),
        Paragraph(
            f"Supplier: {supplier_name} - {labels['tax_id_label']}: {invoice.supplier_tax_id}",
            styles["Normal"],
        ),
        Paragraph(
            f"Buyer: {company_name} - {labels['tax_id_label']}: {company_tax_id}",
            styles["Normal"],
        ),
        Paragraph(f"Issue date: {invoice.issue_date.isoformat()}", styles["Normal"]),
    ]
    if invoice.due_date is not None:
        elements.append(Paragraph(f"Due date: {invoice.due_date.isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_line_items_table(invoice.lines))
    elements.append(Spacer(1, 6 * mm))

    for tax in invoice.taxes:
        elements.append(Paragraph(
            f"{tax.tax_type} {_percent(tax.rate):.0f}%: {_money(tax.amount)}",
            styles["Normal"],
        ))
    for withholding in invoice.withholdings:
        elements.append(Paragraph(
            f"Withholding ({withholding.kind}) {_percent(withholding.rate):.0f}%: "
            f"{_money(withholding.amount)}",
            styles["Normal"],
        ))

    elements.append(Spacer(1, 4 * mm))
    subtotal_text = f"Subtotal: {_converted_money(invoice.subtotal)}"
    elements.append(Paragraph(subtotal_text, styles["Normal"]))
    total_text = f"Total: {_converted_money(invoice.total)}"
    elements.append(Paragraph(total_text, styles["Normal"]))
    payable_text = f"Payable: {_money(invoice.payable)}"
    elements.append(Paragraph(payable_text, styles["Normal"]))
    elements.append(Spacer(1, 4 * mm))
    account_text = f"Bank account: {invoice.bank_account.account_number}"
    elements.append(Paragraph(account_text, styles["Normal"]))

    return _build_pdf(elements)


def render_credit_note_pdf(
    credit_note: CanonicalCreditNote, supplier_name: str, company_name: str, jurisdiction: str,
) -> bytes:
    styles = getSampleStyleSheet()

    elements = [
        Paragraph(f"CREDIT NOTE {credit_note.credit_note_key}", styles["Title"]),
        Spacer(1, 6 * mm),
        Paragraph(
            f"References invoice: {credit_note.references_invoice_key}", styles["Normal"],
        ),
        Paragraph(f"Supplier: {supplier_name}", styles["Normal"]),
        Paragraph(f"Buyer: {company_name}", styles["Normal"]),
        Paragraph(
            f"Scope: {credit_note.scope} - Reason: {credit_note.reason_code}",
            styles["Normal"],
        ),
    ]
    if credit_note.es_rectification_mode is not None:
        elements.append(Paragraph(
            f"Rectification mode: {credit_note.es_rectification_mode}", styles["Normal"],
        ))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_line_items_table(credit_note.lines))
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        f"Total: {_converted_money(credit_note.total)}",
        styles["Normal"],
    ))

    return _build_pdf(elements)
