from typing import Any, Dict, List

import pytest

from maxpybot.dispatcher.filters import (
    callback_payload_is,
    chat_type_is,
    sender_id_is,
    text_contains,
    text_matches,
)
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
async def test_router_middleware_pipeline_hooks() -> None:
    router = Router()
    events: List[str] = []

    @router.middleware_before()
    def on_before(update: Any) -> None:
        events.append("before")

    @router.middleware_after()
    def on_after(update: Any, handled: bool) -> None:
        events.append("after:{0}".format(handled))

    @router.message()
    async def on_message(update: Any) -> None:
        events.append("handler")

    handled = await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {"body": {"text": "hello"}},
        }
    )

    assert handled is True
    assert events == ["before", "handler", "after:True"]


@pytest.mark.asyncio
async def test_router_error_handler_chain_for_nested_routers() -> None:
    parent = Router()
    child = Router()
    parent.include_router(child)

    events: List[str] = []

    @child.middleware_error()
    def child_error_hook(update: Any, error: Exception) -> None:
        events.append("child-hook:{0}".format(error))

    @parent.on_error()
    def parent_error_handler(update: Any, error: Exception) -> None:
        events.append("parent-handler:{0}".format(error))

    calls: List[str] = []

    @child.message()
    async def broken(update: Any) -> None:
        raise ValueError("boom")

    @child.message(text_contains("ok"))
    async def after_error(update: Any) -> None:
        calls.append("ok")

    handled = await parent.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {"body": {"text": "ok"}},
        }
    )

    assert handled is True
    assert calls == ["ok"]
    assert events == ["child-hook:boom", "parent-handler:boom"]


@pytest.mark.asyncio
async def test_extended_filters_for_chat_sender_callback_and_regex() -> None:
    router = Router()
    calls: List[str] = []

    @router.message(
        chat_type_is("chat"),
        sender_id_is(42),
        text_matches(r"^hello\s+\w+$"),
    )
    async def on_chat_message(update: Any) -> None:
        calls.append("message")

    @router.callback_query(callback_payload_is("approve"))
    async def on_callback(update: Any) -> None:
        calls.append("callback")

    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {
                "body": {"text": "hello world"},
                "recipient": {"chat_id": 1, "chat_type": "chat"},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 2,
            "message": {
                "body": {"text": "hello world"},
                "recipient": {"chat_id": 1, "chat_type": "dialog"},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_callback",
            "timestamp": 3,
            "callback": {"payload": "approve"},
        }
    )
    await router.dispatch(
        {
            "update_type": "message_callback",
            "timestamp": 4,
            "callback": {"payload": "reject"},
        }
    )

    assert calls == ["message", "callback"]


@pytest.mark.asyncio
async def test_polling_runner_lifecycle_hooks_and_stop() -> None:
    class FakeApi:
        async def iter_updates(self, marker=None, types=None):  # noqa: ANN001
            yield {"update_type": "message_created", "timestamp": 1, "message": {"body": {"text": "first"}}}
            yield {"update_type": "message_created", "timestamp": 2, "message": {"body": {"text": "second"}}}

    router = Router()
    runner = PollingRunner(api=FakeApi(), router=router)
    lifecycle: List[str] = []
    handled_messages: List[str] = []

    @runner.on_start()
    def on_start() -> None:
        lifecycle.append("start")

    @runner.on_stop()
    async def on_stop() -> None:
        lifecycle.append("stop")

    @runner.on_shutdown()
    def on_shutdown() -> None:
        lifecycle.append("shutdown")

    @router.message()
    async def on_message(update: Any) -> None:
        handled_messages.append(update["message"]["body"]["text"])
        runner.stop()

    await runner.run()

    assert lifecycle == ["start", "stop", "shutdown"]
    assert handled_messages == ["first"]
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
