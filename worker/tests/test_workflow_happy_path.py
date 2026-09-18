import uuid
from decimal import Decimal

import pytest
from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from worker.workflows import TASK_QUEUE, InvoiceWorkflow

from tests.conftest import make_fake_activities

pytestmark = pytest.mark.asyncio


async def test_happy_path_runs_every_step_in_order_with_no_compensation():
    calls: list[str] = []
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter
    ) as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[InvoiceWorkflow],
            activities=make_fake_activities(calls),
        ):
            payload = InvoiceDemoPayload(
                invoice_id="inv-1",
                company_id="company-1",
                amount=Money(amount=Decimal("100.00"), currency="PEN"),
            )
            result = await env.client.execute_workflow(
                InvoiceWorkflow.run,
                payload,
                id=f"test-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

    assert result == "completed"
    assert calls == [
        "validate_invoice",
        "reserve_budget",
        "post_to_erp",
        "schedule_payment",
        "confirm_payment",
    ]
