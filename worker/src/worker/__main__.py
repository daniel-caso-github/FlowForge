import asyncio
import os

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from worker.activities import (
    confirm_payment,
    post_to_erp,
    release_budget,
    reserve_budget,
    schedule_payment,
    validate_invoice,
    void_erp_post,
)
from worker.workflows import TASK_QUEUE, InvoiceWorkflow

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")


async def main() -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, data_converter=pydantic_data_converter)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[InvoiceWorkflow],
        activities=[
            validate_invoice,
            reserve_budget,
            release_budget,
            post_to_erp,
            void_erp_post,
            schedule_payment,
            confirm_payment,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
