import hashlib
from datetime import date, timedelta
from decimal import Decimal
from uuid import NAMESPACE_DNS, uuid5

from flowforge_contracts.bank_account import BankAccountRef
from flowforge_contracts.canonical_invoice import CanonicalInvoice
from flowforge_contracts.converted_money import ConvertedMoney
from flowforge_contracts.invoice_line import InvoiceLine
from flowforge_contracts.money import Money
from jurisdiction_packs.protocol import JurisdictionPack

from datagen.master_data import Company, Product, Supplier


def build_invoice(
    pack: JurisdictionPack,
    company: Company,
    supplier: Supplier,
    products: list[Product],
    series_number: str,
    issue_date: date,
    currency_override: str | None = None,
) -> CanonicalInvoice:
    currency = currency_override or products[0].currency
    lines = [
        InvoiceLine(
            line_number=i + 1, description=product.description, quantity=Decimal("1"),
            unit_price=Money(amount=product.unit_price, currency=currency),
            line_total=Money(amount=product.unit_price, currency=currency),
        )
        for i, product in enumerate(products)
    ]
    subtotal_amount = sum((line.line_total.amount for line in lines), Decimal("0"))

    fingerprint = hashlib.sha256(supplier.bank_account_number.encode()).hexdigest()
    bank_account = BankAccountRef(
        last4=supplier.bank_account_number[-4:], fingerprint=fingerprint,
        account_number=supplier.bank_account_number,
    )

    def _converted(amount: Decimal) -> ConvertedMoney:
        return ConvertedMoney(
            original=Money(amount=amount, currency=currency),
            base=Money(amount=amount, currency=currency), rate=Decimal("1"),
            rate_date=issue_date, rate_source="datagen-simulated",
        )

    invoice_key = f"{company.id}:{supplier.tax_id}:{series_number}"
    source_extraction_id = uuid5(NAMESPACE_DNS, f"extraction:{invoice_key}")

    draft = CanonicalInvoice(
        invoice_key=invoice_key,
        company_id=company.id, jurisdiction=pack.code, supplier_tax_id=supplier.tax_id,
        series_number=series_number, issue_date=issue_date,
        due_date=issue_date + timedelta(days=30),
        po_reference=None, lines=lines, subtotal=_converted(subtotal_amount),
        taxes=[], withholdings=[], total=_converted(subtotal_amount),
        payable=Money(amount=subtotal_amount, currency=currency),
        bank_account=bank_account, source_extraction_id=source_extraction_id,
    )

    taxes = pack.expected_taxes(draft)
    tax_total = sum((t.amount.amount for t in taxes), Decimal("0"))
    withholdings = pack.withholdings(draft, supplier.profile, company)
    withholding_total = sum((w.amount.amount for w in withholdings), Decimal("0"))
    total_amount = subtotal_amount + tax_total
    payable_amount = total_amount - withholding_total

    return draft.model_copy(update={
        "taxes": taxes,
        "withholdings": withholdings,
        "total": _converted(total_amount),
        "payable": Money(amount=payable_amount, currency=currency),
    })
