from typing import Any, Dict, List

import pytest

from maxpybot.dispatcher.filters import text_contains
from maxpybot.dispatcher.polling import PollingRunner
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookHandler


@pytest.mark.asyncio
async def test_router_message_filter_dispatch() -> None:
    router = Router()
    handled: List[Dict[str, Any]] = []

    @router.message(text_contains("hello"))
    async def on_message(update: Any) -> None:
        if hasattr(update, "model_dump"):
            handled.append(update.model_dump(by_alias=True))
        else:
            handled.append(update)

    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {"body": {"text": "hello world"}},
        }
    )

    assert len(handled) == 1


@pytest.mark.asyncio
async def test_polling_runner_dispatches_updates() -> None:
    class FakeApi:
        async def iter_updates(self, marker=None, types=None):  # noqa: ANN001
            yield {"update_type": "message_created", "timestamp": 1, "message": {"body": {"text": "ping"}}}

    router = Router()
    calls: List[str] = []

    @router.message(text_contains("ping"))
    async def on_message(update: Any) -> None:
        calls.append("ok")

    runner = PollingRunner(api=FakeApi(), router=router)
    await runner.run()
    assert calls == ["ok"]
    assert runner.running is False


@pytest.mark.asyncio
async def test_webhook_handler_success_and_errors() -> None:
    router = Router()
    calls: List[str] = []

    @router.message()
    async def on_message(update: Any) -> None:
        calls.append("handled")

    handler = WebhookHandler(router)

    class FakeRequest:
        def __init__(self, method: str, payload: Dict[str, Any] = None, raises: Exception = None) -> None:
            self.method = method
            self._payload = payload or {}
            self._raises = raises

        async def json(self) -> Dict[str, Any]:
            if self._raises is not None:
                raise self._raises
            return self._payload

    wrong_method_resp = await handler.handle(FakeRequest("GET"))
    assert wrong_method_resp.status == 405

    bad_json_resp = await handler.handle(FakeRequest("POST", raises=ValueError("bad json")))
    assert bad_json_resp.status == 400

    ok_resp = await handler.handle(
        FakeRequest(
            "POST",
            payload={
                "update_type": "message_created",
                "timestamp": 1,
                "message": {"body": {"text": "hello"}},
            },
        )
    )
    assert ok_resp.status == 200
    assert calls == ["handled"]
