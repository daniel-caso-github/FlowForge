import pytest
from temporalio import activity


@pytest.fixture
def fake_activities_factory():
    return make_fake_activities


def make_fake_activities(calls: list[str], fail_at: str | None = None):
    @activity.defn(name="validate_invoice")
    async def validate_invoice(payload) -> None:
        calls.append("validate_invoice")
        _maybe_raise("validate_invoice", fail_at)

    @activity.defn(name="reserve_budget")
    async def reserve_budget(payload) -> None:
        calls.append("reserve_budget")
        _maybe_raise("reserve_budget", fail_at)

    @activity.defn(name="release_budget")
    async def release_budget(payload) -> None:
        calls.append("release_budget")

    @activity.defn(name="post_to_erp")
    async def post_to_erp(payload) -> None:
        calls.append("post_to_erp")
        _maybe_raise("post_to_erp", fail_at)

    @activity.defn(name="void_erp_post")
    async def void_erp_post(payload) -> None:
        calls.append("void_erp_post")

    @activity.defn(name="schedule_payment")
    async def schedule_payment(payload) -> None:
        calls.append("schedule_payment")
        _maybe_raise("schedule_payment", fail_at)

    @activity.defn(name="confirm_payment")
    async def confirm_payment(payload) -> None:
        calls.append("confirm_payment")
        _maybe_raise("confirm_payment", fail_at)

    return [
        validate_invoice,
        reserve_budget,
        release_budget,
        post_to_erp,
        void_erp_post,
        schedule_payment,
        confirm_payment,
    ]


def _maybe_raise(activity_name: str, fail_at: str | None) -> None:
    if fail_at == activity_name:
        from temporalio.exceptions import ApplicationError

        raise ApplicationError(f"forced failure at {activity_name}", non_retryable=True)
