import uuid
from decimal import Decimal

import pytest
from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from tests.conftest import make_fake_activities
from worker.workflows import TASK_QUEUE, InvoiceWorkflow

pytestmark = pytest.mark.asyncio


async def test_completed_workflow_history_replays_without_error():
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
            workflow_id = f"test-{uuid.uuid4()}"
            handle = await env.client.start_workflow(
                InvoiceWorkflow.run,
                payload,
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )
            await handle.result()

            history = await handle.fetch_history()

    replayer = Replayer(workflows=[InvoiceWorkflow], data_converter=pydantic_data_converter)
    await replayer.replay_workflow(history)
