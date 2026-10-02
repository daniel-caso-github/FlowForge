from decimal import Decimal
from io import BytesIO

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LABELS: dict[str, dict[str, str]] = {
    "PE": {"tax_id_label": "RUC", "tax_label": "IGV", "currency_symbol": "S/"},
    "ES": {"tax_id_label": "NIF/CIF", "tax_label": "IVA", "currency_symbol": "EUR"},
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


def _money(amount: Decimal, symbol: str) -> str:
    return f"{symbol} {amount:.2f}"


def _line_items_table(lines, symbol: str) -> Table:
    rows = [_LINE_HEADER]
    for line in lines:
        rows.append([
            str(line.line_number), line.description, str(line.quantity),
            _money(line.unit_price.amount, symbol), _money(line.line_total.amount, symbol),
        ])
    return Table(rows, style=TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))


def render_invoice_pdf(invoice: CanonicalInvoice, supplier_name: str, company_name: str) -> bytes:
    labels = LABELS[invoice.jurisdiction]
    symbol = labels["currency_symbol"]
    styles = getSampleStyleSheet()

    elements = [
        Paragraph(f"INVOICE {invoice.series_number}", styles["Title"]),
        Spacer(1, 6 * mm),
        Paragraph(
            f"Supplier: {supplier_name} - {labels['tax_id_label']}: {invoice.supplier_tax_id}",
            styles["Normal"],
        ),
        Paragraph(f"Buyer: {company_name}", styles["Normal"]),
        Paragraph(f"Issue date: {invoice.issue_date.isoformat()}", styles["Normal"]),
        Spacer(1, 6 * mm),
        _line_items_table(invoice.lines, symbol),
        Spacer(1, 6 * mm),
    ]

    for tax in invoice.taxes:
        elements.append(Paragraph(
            f"{labels['tax_label']} ({tax.tax_type}) {tax.rate * 100:.0f}%: "
            f"{_money(tax.amount.amount, symbol)}",
            styles["Normal"],
        ))
    for withholding in invoice.withholdings:
        elements.append(Paragraph(
            f"Withholding ({withholding.kind}) {withholding.rate * 100:.0f}%: "
            f"{_money(withholding.amount.amount, symbol)}",
            styles["Normal"],
        ))

    elements.append(Spacer(1, 4 * mm))
    subtotal_text = f"Subtotal: {_money(invoice.subtotal.original.amount, symbol)}"
    elements.append(Paragraph(subtotal_text, styles["Normal"]))
    total_text = f"Total: {_money(invoice.total.original.amount, symbol)}"
    elements.append(Paragraph(total_text, styles["Normal"]))
    payable_text = f"Payable: {_money(invoice.payable.amount, symbol)}"
    elements.append(Paragraph(payable_text, styles["Normal"]))
    elements.append(Spacer(1, 4 * mm))
    account_text = f"Bank account: {invoice.bank_account.account_number}"
    elements.append(Paragraph(account_text, styles["Normal"]))

    return _build_pdf(elements)


def render_credit_note_pdf(
    credit_note: CanonicalCreditNote, supplier_name: str, company_name: str, jurisdiction: str,
) -> bytes:
    labels = LABELS[jurisdiction]
    symbol = labels["currency_symbol"]
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
        Spacer(1, 6 * mm),
        _line_items_table(credit_note.lines, symbol),
        Spacer(1, 6 * mm),
        Paragraph(
            f"Total: {_money(credit_note.total.original.amount, symbol)}",
            styles["Normal"],
        ),
    ]

    return _build_pdf(elements)
