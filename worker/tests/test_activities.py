from decimal import Decimal

import httpx
import pytest
import respx
from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money
from temporalio.exceptions import ApplicationError
from temporalio.testing import ActivityEnvironment
from worker.activities import reserve_budget, schedule_payment, validate_invoice

pytestmark = pytest.mark.asyncio


async def test_reserve_budget_posts_to_budget_service_with_idempotency_key():
    env = ActivityEnvironment()
    workflow_id = env.info.workflow_id
    payload = InvoiceDemoPayload(
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )

    with respx.mock(base_url="http://localhost:8001") as mock:
        route = mock.post("/reservations").mock(
            return_value=httpx.Response(
                200, json={"idempotency_key": f"{workflow_id}-reserve_budget", "status": "reserved"}
            )
        )
        await env.run(reserve_budget, payload)

    assert route.called
    sent_body = route.calls.last.request.content.decode()
    assert f"{workflow_id}-reserve_budget" in sent_body


async def test_validate_invoice_raises_non_retryable_when_fail_at_matches():
    env = ActivityEnvironment()
    payload = InvoiceDemoPayload(
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
        fail_at="validate_invoice",
    )

    with pytest.raises(ApplicationError) as exc_info:
        await env.run(validate_invoice, payload)
    assert exc_info.value.non_retryable is True


async def test_schedule_payment_posts_to_external_sim():
    env = ActivityEnvironment()
    workflow_id = env.info.workflow_id
    payload = InvoiceDemoPayload(
        invoice_id="inv-1",
        company_id="company-1",
        amount=Money(amount=Decimal("100.00"), currency="PEN"),
    )

    with respx.mock(base_url="http://localhost:8002") as mock:
        route = mock.post("/payments/schedule").mock(
            return_value=httpx.Response(
                200,
                json={"idempotency_key": f"{workflow_id}-schedule_payment", "status": "scheduled"},
            )
        )
        await env.run(schedule_payment, payload)

    assert route.called
