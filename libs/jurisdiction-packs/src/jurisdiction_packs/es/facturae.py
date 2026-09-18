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

FACTURAE_NS = "http://www.facturae.es/Facturae/2014/v3.2.1/Facturae"
FF_NS = "urn:flowforge:extensions:1.0"

ET.register_namespace("fe", FACTURAE_NS)
ET.register_namespace("ff", FF_NS)

_WITHHOLDINGS_ADAPTER = TypeAdapter(list[WithholdingLine])


def _fe(tag: str) -> str:
    return f"{{{FACTURAE_NS}}}{tag}"


def _ff(tag: str) -> str:
    return f"{{{FF_NS}}}{tag}"


def generate_xml(invoice: CanonicalInvoice) -> bytes:
    root = ET.Element(_fe("Facturae"))
    ET.SubElement(ET.SubElement(root, _fe("FileHeader")), _fe("SchemaVersion")).text = "3.2.1"

    seller = ET.SubElement(ET.SubElement(root, _fe("Parties")), _fe("SellerParty"))
    tax_identification = ET.SubElement(seller, _fe("TaxIdentification"))
    tax_id_el = ET.SubElement(tax_identification, _fe("TaxIdentificationNumber"))
    tax_id_el.text = invoice.supplier_tax_id

    invoice_el = ET.SubElement(ET.SubElement(root, _fe("Invoices")), _fe("Invoice"))
    invoice_header = ET.SubElement(invoice_el, _fe("InvoiceHeader"))
    ET.SubElement(invoice_header, _fe("InvoiceNumber")).text = invoice.series_number

    issue_data = ET.SubElement(invoice_el, _fe("InvoiceIssueData"))
    ET.SubElement(issue_data, _fe("IssueDate")).text = invoice.issue_date.isoformat()
    if invoice.due_date is not None:
        ET.SubElement(issue_data, _fe("InvoiceDueDate")).text = invoice.due_date.isoformat()
    ET.SubElement(issue_data, _fe("InvoiceCurrencyCode")).text = invoice.payable.currency

    taxes_el = ET.SubElement(invoice_el, _fe("TaxesOutputs"))
    for tax in invoice.taxes:
        tax_el = ET.SubElement(taxes_el, _fe("Tax"))
        ET.SubElement(tax_el, _fe("TaxTypeCode")).text = tax.tax_type
        ET.SubElement(tax_el, _fe("TaxRate")).text = str(tax.rate)
        taxable_base = ET.SubElement(tax_el, _fe("TaxableBase"))
        ET.SubElement(taxable_base, _fe("TotalAmount")).text = str(tax.base.amount)
        tax_amount = ET.SubElement(tax_el, _fe("TaxAmount"))
        ET.SubElement(tax_amount, _fe("TotalAmount")).text = str(tax.amount.amount)

    items_el = ET.SubElement(invoice_el, _fe("Items"))
    for line in invoice.lines:
        line_el = ET.SubElement(items_el, _fe("InvoiceLine"))
        ET.SubElement(line_el, _fe("ItemDescription")).text = line.description
        ET.SubElement(line_el, _fe("Quantity")).text = str(line.quantity)
        ET.SubElement(line_el, _fe("UnitPriceWithoutTax")).text = str(line.unit_price.amount)
        ET.SubElement(line_el, _fe("TotalCost")).text = str(line.line_total.amount)

    totals_el = ET.SubElement(invoice_el, _fe("InvoiceTotals"))
    ET.SubElement(totals_el, _fe("InvoiceTotal")).text = str(invoice.payable.amount)

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
    invoice_el = root.find(f"{_fe('Invoices')}/{_fe('Invoice')}")
    series_number = invoice_el.find(f"{_fe('InvoiceHeader')}/{_fe('InvoiceNumber')}").text

    issue_data = invoice_el.find(_fe("InvoiceIssueData"))
    issue_date = date.fromisoformat(issue_data.find(_fe("IssueDate")).text)
    due_date_el = issue_data.find(_fe("InvoiceDueDate"))
    due_date = date.fromisoformat(due_date_el.text) if due_date_el is not None else None
    currency = issue_data.find(_fe("InvoiceCurrencyCode")).text

    supplier_tax_id = root.find(
        f"{_fe('Parties')}/{_fe('SellerParty')}/{_fe('TaxIdentification')}/{_fe('TaxIdentificationNumber')}"
    ).text

    taxes = []
    for tax_el in invoice_el.findall(f"{_fe('TaxesOutputs')}/{_fe('Tax')}"):
        taxable = tax_el.find(f"{_fe('TaxableBase')}/{_fe('TotalAmount')}").text
        amount = tax_el.find(f"{_fe('TaxAmount')}/{_fe('TotalAmount')}").text
        taxes.append(
            TaxLine(
                tax_type=tax_el.find(_fe("TaxTypeCode")).text,
                rate=Decimal(tax_el.find(_fe("TaxRate")).text),
                base=Money(amount=Decimal(taxable), currency=currency),
                amount=Money(amount=Decimal(amount), currency=currency),
            )
        )

    lines = []
    line_elements = invoice_el.findall(f"{_fe('Items')}/{_fe('InvoiceLine')}")
    for i, line_el in enumerate(line_elements, start=1):
        lines.append(
            InvoiceLine(
                line_number=i,
                description=line_el.find(_fe("ItemDescription")).text,
                quantity=Decimal(line_el.find(_fe("Quantity")).text),
                unit_price=Money(
                    amount=Decimal(line_el.find(_fe("UnitPriceWithoutTax")).text), currency=currency
                ),
                line_total=Money(
                    amount=Decimal(line_el.find(_fe("TotalCost")).text), currency=currency
                ),
            )
        )

    payable = Money(
        amount=Decimal(invoice_el.find(f"{_fe('InvoiceTotals')}/{_fe('InvoiceTotal')}").text),
        currency=currency,
    )

    extensions = root.find(_ff("Extensions"))
    po_reference_el = extensions.find(_ff("PoReference"))

    return CanonicalInvoice(
        invoice_key=extensions.find(_ff("InvoiceKey")).text,
        company_id=UUID(extensions.find(_ff("CompanyId")).text),
        jurisdiction="ES",
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
