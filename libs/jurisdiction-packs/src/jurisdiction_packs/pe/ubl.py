from datetime import date
from decimal import Decimal
from uuid import UUID
from xml.etree import ElementTree as ET

from defusedxml.ElementTree import fromstring as safe_fromstring
from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from flowforge_contracts.tax_line import TaxLine
from flowforge_contracts.withholding_line import WithholdingLine
from pydantic import TypeAdapter

UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
FF_NS = "urn:flowforge:extensions:1.0"

ET.register_namespace("cac", CAC_NS)
ET.register_namespace("cbc", CBC_NS)
ET.register_namespace("ff", FF_NS)

_WITHHOLDINGS_ADAPTER = TypeAdapter(list[WithholdingLine])


def _cbc(tag: str) -> str:
    return f"{{{CBC_NS}}}{tag}"


def _cac(tag: str) -> str:
    return f"{{{CAC_NS}}}{tag}"


def _ff(tag: str) -> str:
    return f"{{{FF_NS}}}{tag}"


def generate_xml(invoice: CanonicalInvoice) -> bytes:
    root = ET.Element(f"{{{UBL_NS}}}Invoice")
    ET.SubElement(root, _cbc("ID")).text = invoice.series_number
    ET.SubElement(root, _cbc("IssueDate")).text = invoice.issue_date.isoformat()
    if invoice.due_date is not None:
        ET.SubElement(root, _cbc("DueDate")).text = invoice.due_date.isoformat()
    ET.SubElement(root, _cbc("DocumentCurrencyCode")).text = invoice.payable.currency

    supplier_id = ET.SubElement(
        ET.SubElement(ET.SubElement(root, _cac("AccountingSupplierParty")), _cac("Party")),
        _cac("PartyIdentification"),
    )
    ET.SubElement(supplier_id, _cbc("ID")).text = invoice.supplier_tax_id

    for line in invoice.lines:
        line_el = ET.SubElement(root, _cac("InvoiceLine"))
        ET.SubElement(line_el, _cbc("ID")).text = str(line.line_number)
        ET.SubElement(line_el, _cbc("InvoicedQuantity")).text = str(line.quantity)
        amount_el = ET.SubElement(line_el, _cbc("LineExtensionAmount"))
        amount_el.set("currencyID", line.line_total.currency)
        amount_el.text = str(line.line_total.amount)
        item = ET.SubElement(line_el, _cac("Item"))
        ET.SubElement(item, _cbc("Description")).text = line.description
        price_amount = ET.SubElement(ET.SubElement(line_el, _cac("Price")), _cbc("PriceAmount"))
        price_amount.set("currencyID", line.unit_price.currency)
        price_amount.text = str(line.unit_price.amount)

    tax_total = ET.SubElement(root, _cac("TaxTotal"))
    for tax in invoice.taxes:
        subtotal = ET.SubElement(tax_total, _cac("TaxSubtotal"))
        taxable = ET.SubElement(subtotal, _cbc("TaxableAmount"))
        taxable.set("currencyID", tax.base.currency)
        taxable.text = str(tax.base.amount)
        amount = ET.SubElement(subtotal, _cbc("TaxAmount"))
        amount.set("currencyID", tax.amount.currency)
        amount.text = str(tax.amount.amount)
        category = ET.SubElement(subtotal, _cac("TaxCategory"))
        ET.SubElement(category, _cbc("Percent")).text = str(tax.rate)
        ET.SubElement(ET.SubElement(category, _cac("TaxScheme")), _cbc("ID")).text = tax.tax_type

    payable_el = ET.SubElement(ET.SubElement(root, _cac("LegalMonetaryTotal")), _cbc("PayableAmount"))
    payable_el.set("currencyID", invoice.payable.currency)
    payable_el.text = str(invoice.payable.amount)

    extensions = ET.SubElement(root, _ff("Extensions"))
    ET.SubElement(extensions, _ff("InvoiceKey")).text = invoice.invoice_key
    ET.SubElement(extensions, _ff("CompanyId")).text = str(invoice.company_id)
    if invoice.po_reference is not None:
        ET.SubElement(extensions, _ff("PoReference")).text = invoice.po_reference
    ET.SubElement(extensions, _ff("Subtotal")).text = invoice.subtotal.model_dump_json()
    ET.SubElement(extensions, _ff("Total")).text = invoice.total.model_dump_json()
    ET.SubElement(extensions, _ff("Withholdings")).text = _WITHHOLDINGS_ADAPTER.dump_json(
        invoice.withholdings
    ).decode()
    ET.SubElement(extensions, _ff("BankAccount")).text = invoice.bank_account.model_dump_json()
    ET.SubElement(extensions, _ff("SourceExtractionId")).text = str(invoice.source_extraction_id)

    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")


def parse_structured(xml: bytes) -> CanonicalInvoice:
    root = safe_fromstring(xml)
    series_number = root.find(_cbc("ID")).text
    issue_date = date.fromisoformat(root.find(_cbc("IssueDate")).text)
    due_date_el = root.find(_cbc("DueDate"))
    due_date = date.fromisoformat(due_date_el.text) if due_date_el is not None else None

    supplier_tax_id = root.find(
        f"{_cac('AccountingSupplierParty')}/{_cac('Party')}/{_cac('PartyIdentification')}/{_cbc('ID')}"
    ).text

    lines = []
    for line_el in root.findall(_cac("InvoiceLine")):
        line_total_el = line_el.find(_cbc("LineExtensionAmount"))
        price_el = line_el.find(f"{_cac('Price')}/{_cbc('PriceAmount')}")
        lines.append(
            InvoiceLine(
                line_number=int(line_el.find(_cbc("ID")).text),
                description=line_el.find(f"{_cac('Item')}/{_cbc('Description')}").text,
                quantity=Decimal(line_el.find(_cbc("InvoicedQuantity")).text),
                unit_price=Money(amount=Decimal(price_el.text), currency=price_el.get("currencyID")),
                line_total=Money(
                    amount=Decimal(line_total_el.text), currency=line_total_el.get("currencyID")
                ),
            )
        )

    taxes = []
    for subtotal_el in root.findall(f"{_cac('TaxTotal')}/{_cac('TaxSubtotal')}"):
        taxable_el = subtotal_el.find(_cbc("TaxableAmount"))
        amount_el = subtotal_el.find(_cbc("TaxAmount"))
        percent_el = subtotal_el.find(f"{_cac('TaxCategory')}/{_cbc('Percent')}")
        tax_type_el = subtotal_el.find(f"{_cac('TaxCategory')}/{_cac('TaxScheme')}/{_cbc('ID')}")
        taxes.append(
            TaxLine(
                tax_type=tax_type_el.text, rate=Decimal(percent_el.text),
                base=Money(amount=Decimal(taxable_el.text), currency=taxable_el.get("currencyID")),
                amount=Money(amount=Decimal(amount_el.text), currency=amount_el.get("currencyID")),
            )
        )

    payable_el = root.find(f"{_cac('LegalMonetaryTotal')}/{_cbc('PayableAmount')}")
    payable = Money(amount=Decimal(payable_el.text), currency=payable_el.get("currencyID"))

    extensions = root.find(_ff("Extensions"))
    po_reference_el = extensions.find(_ff("PoReference"))

    return CanonicalInvoice(
        invoice_key=extensions.find(_ff("InvoiceKey")).text,
        company_id=UUID(extensions.find(_ff("CompanyId")).text),
        jurisdiction="PE",
        supplier_tax_id=supplier_tax_id,
        series_number=series_number,
        issue_date=issue_date,
        due_date=due_date,
        po_reference=po_reference_el.text if po_reference_el is not None else None,
        lines=lines,
        subtotal=ConvertedMoney.model_validate_json(extensions.find(_ff("Subtotal")).text),
        taxes=taxes,
        withholdings=_WITHHOLDINGS_ADAPTER.validate_json(extensions.find(_ff("Withholdings")).text),
        total=ConvertedMoney.model_validate_json(extensions.find(_ff("Total")).text),
        payable=payable,
        bank_account=BankAccountRef.model_validate_json(extensions.find(_ff("BankAccount")).text),
        source_extraction_id=UUID(extensions.find(_ff("SourceExtractionId")).text),
    )
