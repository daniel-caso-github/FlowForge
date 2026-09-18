from datetime import timedelta

from flowforge_contracts.invoice import InvoiceDemoPayload
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from worker.activities import (
        confirm_payment,
        post_to_erp,
        release_budget,
        reserve_budget,
        schedule_payment,
        validate_invoice,
        void_erp_post,
    )

TASK_QUEUE = "invoice-task-queue"
ACTIVITY_TIMEOUT = timedelta(seconds=10)


@workflow.defn
class InvoiceWorkflow:
    @workflow.run
    async def run(self, payload: InvoiceDemoPayload) -> str:
        compensations: list = []
        try:
            await workflow.execute_activity(
                validate_invoice, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
            )

            await workflow.execute_activity(
                reserve_budget, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
            )
            compensations.append(release_budget)

            await workflow.execute_activity(
                post_to_erp, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
            )
            compensations.append(void_erp_post)

            await workflow.execute_activity(
                schedule_payment, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
            )
            compensations.clear()  # pivot passed: retries only from here (ADR-002)

            await workflow.execute_activity(
                confirm_payment, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
            )
            return "completed"
        except Exception:
            for compensate in reversed(compensations):
                await workflow.execute_activity(
                    compensate, payload, start_to_close_timeout=ACTIVITY_TIMEOUT
                )
            raise
