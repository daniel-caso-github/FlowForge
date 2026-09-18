from decimal import Decimal

from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money


def test_invoice_demo_payload_defaults_have_no_injected_failure():
    payload = InvoiceDemoPayload(
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )
    assert payload.fail_at is None
    assert payload.delay_at is None
    assert payload.delay_seconds == 0


def test_invoice_demo_payload_carries_fail_at():
    payload = InvoiceDemoPayload(
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
        fail_at="post_to_erp",
    )
    assert payload.fail_at == "post_to_erp"
