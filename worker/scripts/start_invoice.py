import argparse
import asyncio
import uuid
from decimal import Decimal

from flowforge_contracts.invoice import InvoiceDemoPayload
from flowforge_contracts.money import Money
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from worker.workflows import TASK_QUEUE, InvoiceWorkflow

TEMPORAL_ADDRESS = "localhost:7233"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a demo InvoiceWorkflow")
    parser.add_argument("--invoice-id", default=f"demo-{uuid.uuid4()}")
    parser.add_argument("--company-id", default="company-demo")
    parser.add_argument("--amount", default="100.00")
    parser.add_argument("--currency", default="PEN")
    parser.add_argument("--fail-at", default=None)
    parser.add_argument("--delay-at", default=None)
    parser.add_argument("--delay-seconds", type=int, default=0)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    client = await Client.connect(TEMPORAL_ADDRESS, data_converter=pydantic_data_converter)
    payload = InvoiceDemoPayload(
        invoice_id=args.invoice_id,
        company_id=args.company_id,
        amount=Money(amount=Decimal(args.amount), currency=args.currency),
        fail_at=args.fail_at,
        delay_at=args.delay_at,
        delay_seconds=args.delay_seconds,
    )
    handle = await client.start_workflow(
        InvoiceWorkflow.run,
        payload,
        id=args.invoice_id,
        task_queue=TASK_QUEUE,
    )
    print(f"started workflow {handle.id}")
    result = await handle.result()
    print(f"workflow finished: {result}")


if __name__ == "__main__":
    asyncio.run(main())
