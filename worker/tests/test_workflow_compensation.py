import uuid
from decimal import Decimal

import pytest
from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money
from temporalio.client import WorkflowFailureError
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from worker.workflows import TASK_QUEUE, InvoiceWorkflow

pytestmark = pytest.mark.asyncio


async def test_forced_failure_before_pivot_compensates_in_reverse_order(
    fake_activities_factory,
):
    calls: list[str] = []
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[InvoiceWorkflow],
            activities=fake_activities_factory(calls, fail_at="post_to_erp"),
        ):
            payload = InvoiceDemoPayload(
                invoice_id="inv-1",
                company_id="company-1",
                amount=Money(amount=Decimal("100.00"), currency="PEN"),
                fail_at="post_to_erp",
            )
            with pytest.raises(WorkflowFailureError):
                await env.client.execute_workflow(
                    InvoiceWorkflow.run,
                    payload,
                    id=f"test-{uuid.uuid4()}",
                    task_queue=TASK_QUEUE,
                )

    assert calls == ["validate_invoice", "reserve_budget", "post_to_erp", "release_budget"]


async def test_failure_after_pivot_does_not_compensate(fake_activities_factory):
    calls: list[str] = []
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[InvoiceWorkflow],
            activities=fake_activities_factory(calls, fail_at="confirm_payment"),
        ):
            payload = InvoiceDemoPayload(
                invoice_id="inv-1",
                company_id="company-1",
                amount=Money(amount=Decimal("100.00"), currency="PEN"),
                fail_at="confirm_payment",
            )
            with pytest.raises(WorkflowFailureError):
                await env.client.execute_workflow(
                    InvoiceWorkflow.run,
                    payload,
                    id=f"test-{uuid.uuid4()}",
                    task_queue=TASK_QUEUE,
                )

    assert "release_budget" not in calls
    assert "void_erp_post" not in calls
    assert calls == [
        "validate_invoice",
        "reserve_budget",
        "post_to_erp",
        "schedule_payment",
        "confirm_payment",
    ]
