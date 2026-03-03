import ssl
from typing import Any, Dict, List

import pytest

from maxpybot.dispatcher.context import HandlerContext
from maxpybot.dispatcher.dispatcher import Dispatcher
from maxpybot.dispatcher.filters import (
    F,
    callback_payload_is,
    chat_type_is,
    has_start_payload,
    message_has_sticker,
    message_has_text,
    sender_id_is,
    start_payload_is,
    start_payload_matches,
    text_contains,
    text_matches,
)
from maxpybot.dispatcher.polling import PollingRunner
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import (
    WEBHOOK_HANDLER_APP_KEY,
    WEBHOOK_SECRET_HEADER,
    WebhookHandler,
    WebhookMetrics,
    create_https_ssl_context,
    create_webhook_app,
)
from maxpybot.fsm import FSMContext, MemoryStorage, create_fsm_context
from maxpybot.types import Callback, Message


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
async def test_router_injects_typed_message_and_context() -> None:
    router = Router()
    captured: Dict[str, Any] = {}

    @router.message_created()
    async def on_message(message: Message, context: HandlerContext) -> None:
        captured["chat_id"] = message.chat.chat_id
        captured["update_type"] = getattr(context.update, "update_type", context.update.get("update_type"))

    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {
                "sender": {"user_id": 42},
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
                "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
                "timestamp": 1,
            },
        }
    )

    assert captured["chat_id"] == 200
    assert captured["update_type"] == "message_created"


@pytest.mark.asyncio
async def test_router_injects_callback_fsm_and_state() -> None:
    storage = MemoryStorage()
    router = Router(storage=storage)
    calls: List[str] = []

    fsm = create_fsm_context(storage=storage, chat_id=200, user_id=42)
    await fsm.set_state("awaiting_confirm")

    @router.message_callback(state="awaiting_confirm")
    async def on_callback(callback: Callback, message: Message, fsm: FSMContext, state: str) -> None:
        calls.append(
            "{0}:{1}:{2}".format(
                callback.payload,
                message.chat.chat_id,
                state,
            )
        )
        await fsm.clear()

    await router.dispatch(
        {
            "update_type": "message_callback",
            "timestamp": 1,
            "callback": {
                "callback_id": "cb-1",
                "payload": "approve",
                "timestamp": 1,
                "user": {
                    "first_name": "A",
                    "is_bot": False,
                    "last_activity_time": 1,
                    "last_name": "B",
                    "user_id": "42",
                    "username": "alice",
                },
            },
            "message": {
                "sender": {"user_id": 42},
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
                "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
                "timestamp": 1,
            },
        }
    )

    assert calls == ["approve:200:awaiting_confirm"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("decorator_name", "update_type"),
    [
        ("message_created", "message_created"),
        ("message_callback", "message_callback"),
        ("message_edited", "message_edited"),
        ("message_removed", "message_removed"),
        ("bot_added", "bot_added"),
        ("bot_removed", "bot_removed"),
        ("user_added", "user_added"),
        ("user_removed", "user_removed"),
        ("bot_started", "bot_started"),
        ("bot_stopped", "bot_stopped"),
        ("chat_title_changed", "chat_title_changed"),
        ("message_chat_created", "message_chat_created"),
        ("dialog_muted", "dialog_muted"),
        ("dialog_unmuted", "dialog_unmuted"),
        ("dialog_cleared", "dialog_cleared"),
        ("dialog_removed", "dialog_removed"),
    ],
)
async def test_explicit_router_decorators_match_only_target_update_type(
    decorator_name: str,
    update_type: str,
) -> None:
    router = Router()
    calls: List[str] = []

    decorator = getattr(router, decorator_name)

    @decorator()
    async def on_update(update: Any) -> None:
        calls.append(str(getattr(update, "update_type", update.get("update_type"))))

    await router.dispatch({"update_type": update_type, "timestamp": 1})
    await router.dispatch({"update_type": "some_other_update", "timestamp": 1})

    assert calls == [update_type]


def test_router_rejects_unsupported_handler_signature() -> None:
    router = Router()

    with pytest.raises(Exception):
        @router.message_created()
        async def invalid_handler(not_supported: float) -> None:
            return None


@pytest.mark.asyncio
async def test_router_injects_callback_with_message_reference() -> None:
    router = Router()
    calls: List[int] = []

    @router.message_callback()
    async def on_callback(callback: Callback) -> None:
        if callback.message is not None:
            calls.append(callback.message.chat.chat_id)

    await router.dispatch(
        {
            "update_type": "message_callback",
            "timestamp": 1,
            "callback": {
                "callback_id": "cb-1",
                "payload": "approve",
                "timestamp": 1,
                "user": {
                    "first_name": "A",
                    "is_bot": False,
                    "last_activity_time": 1,
                    "last_name": "B",
                    "user_id": "42",
                    "username": "alice",
                },
            },
            "message": {
                "sender": {"user_id": 42},
                "recipient": {"chat_id": 222, "chat_type": "chat", "user_id": 0},
                "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
                "timestamp": 1,
            },
        }
    )

    assert calls == [222]


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
async def test_magic_filters_support_string_ops_composition_and_command_parts() -> None:
    router = Router()
    calls: List[str] = []

    @router.message(
        (F.sender.id.in_({42, 777}))
        & (F.text.startswith("!") | F.text.startswith("/"))
        & F.text.lower().contains("ban")
    )
    async def on_admin_ban(update: Any) -> None:
        calls.append("admin-ban")

    @router.callback_query(F.data.startswith("qst_"))
    async def on_callback(update: Any) -> None:
        calls.append("callback")

    @router.message(F.command == "settings", F.command_args == "fast")
    async def on_settings_command(update: Any) -> None:
        calls.append("command")

    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {
                "body": {"text": "!ban 100"},
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_callback",
            "timestamp": 2,
            "callback": {"payload": "qst_123"},
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 3,
            "message": {
                "body": {"text": "/settings fast"},
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )

    assert calls == ["admin-ban", "callback", "command"]

    long_text_update = {
        "update_type": "message_created",
        "timestamp": 4,
        "message": {
            "body": {"text": "123456"},
            "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
            "sender": {"user_id": "42"},
        },
    }
    assert bool((F.text.len() > 5)(long_text_update)) is True


@pytest.mark.asyncio
async def test_magic_filters_support_start_payload_content_type_and_regex() -> None:
    router = Router()
    calls: List[str] = []

    @router.bot_started(F.start_payload == "promo_summer2025")
    async def on_started(update: Any) -> None:
        calls.append("started")

    @router.message_created(
        F.start_payload.startswith("ref_"),
        F.chat.type.in_({"chat", "dialog"}),
        F.text.regexp(r"^/start\s+\w+$"),
    )
    async def on_start_message(update: Any) -> None:
        calls.append("start-message")

    @router.message_created(F.content_type.in_({"text", "sticker"}))
    async def on_supported_content(update: Any) -> None:
        calls.append("content")

    await router.dispatch(
        {
            "update_type": "bot_started",
            "timestamp": 1,
            "chat_id": 123,
            "user": {
                "first_name": "Ivan",
                "is_bot": False,
                "last_activity_time": 1,
                "last_name": "Petrov",
                "user_id": "100",
                "username": "ivan",
            },
            "payload": "promo_summer2025",
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 2,
            "message": {
                "body": {"text": "/start ref_user456789", "attachments": []},
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 3,
            "message": {
                "body": {
                    "text": "",
                    "attachments": [{"type": "sticker", "payload": {"code": "ok"}}],
                },
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )

    assert calls == ["started", "start-message", "content", "content"]


@pytest.mark.asyncio
async def test_message_content_filters_and_f_namespace() -> None:
    router = Router()
    calls: List[str] = []

    @router.message(message_has_text())
    async def on_text(update: Any) -> None:
        calls.append("text")

    @router.message(F.sticker)
    async def on_sticker(update: Any) -> None:
        calls.append("sticker")

    @router.message(F.video)
    async def on_video(update: Any) -> None:
        calls.append("video")

    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {
                "body": {"text": "hello world", "attachments": []},
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 2,
            "message": {
                "body": {
                    "text": "",
                    "attachments": [{"type": "sticker", "payload": {"code": "smile"}}],
                },
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 3,
            "message": {
                "body": {
                    "text": "",
                    "attachments": [{"type": "video", "payload": {"url": "https://example.com/a.mp4"}}],
                },
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )

    assert calls == ["text", "sticker", "video"]


@pytest.mark.asyncio
async def test_dispatcher_include_routers_and_dispatch() -> None:
    dispatcher = Dispatcher()
    text_router = Router()
    media_router = Router()
    calls: List[str] = []

    @text_router.message(F.text)
    async def on_text(update: Any) -> None:
        calls.append("text")

    @media_router.message(message_has_sticker())
    async def on_sticker(update: Any) -> None:
        calls.append("sticker")

    dispatcher.include_routers(text_router, media_router)

    await dispatcher.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 1,
            "message": {
                "body": {"text": "hello", "attachments": []},
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )
    await dispatcher.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 2,
            "message": {
                "body": {
                    "text": "",
                    "attachments": [{"type": "sticker", "payload": {"code": "ok"}}],
                },
                "recipient": {"chat_id": 1, "chat_type": "chat", "user_id": 0},
                "sender": {"user_id": "42"},
            },
        }
    )

    assert calls == ["text", "sticker"]


@pytest.mark.asyncio
async def test_dispatcher_start_polling_delegates_to_bot() -> None:
    dispatcher = Dispatcher()
    calls: Dict[str, Any] = {}

    class FakeBot:
        async def start_polling(self, router: Router, marker=None, types=None):  # noqa: ANN001
            calls["router"] = router
            calls["marker"] = marker
            calls["types"] = types

    await dispatcher.start_polling(FakeBot(), marker=5, types=["message_created"])  # type: ignore[arg-type]

    assert calls["router"] is dispatcher.router
    assert calls["marker"] == 5
    assert calls["types"] == ["message_created"]


def test_dispatcher_start_webhook_delegates_to_bot() -> None:
    dispatcher = Dispatcher()
    calls: Dict[str, Any] = {}

    class FakeBot:
        def start_webhook(self, **kwargs: Any) -> None:
            calls.update(kwargs)

    dispatcher.start_webhook(
        FakeBot(),  # type: ignore[arg-type]
        path="/webhook",
        host="127.0.0.1",
        port=9000,
        secret="secret",
        update_types=["message_created"],
    )

    assert calls["router"] is dispatcher.router
    assert calls["path"] == "/webhook"
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 9000
    assert calls["secret"] == "secret"
    assert calls["update_types"] == ["message_created"]


@pytest.mark.asyncio
async def test_start_payload_filters_for_bot_started_and_message() -> None:
    router = Router()
    calls: List[str] = []

    @router.bot_started(start_payload_is("promo_summer2025"))
    async def on_bot_started(update: Any) -> None:
        calls.append("started")

    @router.message_created(has_start_payload(), start_payload_matches(r"^ref_"))
    async def on_start_message(message: Message) -> None:
        calls.append(str(message.start_payload))

    await router.dispatch(
        {
            "update_type": "bot_started",
            "timestamp": 1,
            "chat_id": 123,
            "user": {
                "first_name": "Ivan",
                "is_bot": False,
                "last_activity_time": 1,
                "last_name": "Petrov",
                "user_id": "100",
                "username": "ivan",
            },
            "payload": "promo_summer2025",
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 2,
            "message": {
                "sender": {"user_id": 42},
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
                "body": {"mid": "m-1", "seq": 1, "text": "/start ref_user456789", "attachments": []},
                "timestamp": 2,
            },
        }
    )
    await router.dispatch(
        {
            "update_type": "message_created",
            "timestamp": 3,
            "message": {
                "sender": {"user_id": 42},
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
                "body": {"mid": "m-2", "seq": 2, "text": "/start source_site", "attachments": []},
                "timestamp": 3,
            },
        }
    )

    assert calls == ["started", "ref_user456789"]


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
        def __init__(
            self,
            method: str,
            payload: Dict[str, Any] = None,
            raises: Exception = None,
            headers: Dict[str, str] = None,
            remote: str = "",
        ) -> None:
            self.method = method
            self._payload = payload or {}
            self._raises = raises
            self.headers = headers or {}
            self.remote = remote

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


@pytest.mark.asyncio
async def test_webhook_handler_secret_validation() -> None:
    router = Router()
    calls: List[str] = []

    @router.message()
    async def on_message(update: Any) -> None:
        calls.append("handled")

    handler = WebhookHandler(router, secret="my-secret")

    class FakeRequest:
        def __init__(
            self,
            method: str,
            payload: Dict[str, Any] = None,
            headers: Dict[str, str] = None,
            remote: str = "",
        ) -> None:
            self.method = method
            self._payload = payload or {}
            self.headers = headers or {}
            self.remote = remote

        async def json(self) -> Dict[str, Any]:
            return self._payload

    payload = {
        "update_type": "message_created",
        "timestamp": 1,
        "message": {"body": {"text": "hello"}},
    }

    missing_secret_resp = await handler.handle(FakeRequest("POST", payload=payload))
    assert missing_secret_resp.status == 403

    wrong_secret_resp = await handler.handle(
        FakeRequest("POST", payload=payload, headers={WEBHOOK_SECRET_HEADER: "wrong-secret"})
    )
    assert wrong_secret_resp.status == 403

    ok_resp = await handler.handle(
        FakeRequest("POST", payload=payload, headers={WEBHOOK_SECRET_HEADER: "my-secret"})
    )
    assert ok_resp.status == 200
    assert calls == ["handled"]


@pytest.mark.asyncio
async def test_webhook_handler_ip_network_allowlist() -> None:
    router = Router()
    calls: List[str] = []

    @router.message()
    async def on_message(update: Any) -> None:
        calls.append("handled")

    handler = WebhookHandler(
        router,
        allowed_ip_networks=["203.0.113.0/24", "2001:db8::/32"],
    )

    class FakeRequest:
        def __init__(self, method: str, payload: Dict[str, Any], remote: str) -> None:
            self.method = method
            self._payload = payload
            self.headers: Dict[str, str] = {}
            self.remote = remote

        async def json(self) -> Dict[str, Any]:
            return self._payload

    payload = {
        "update_type": "message_created",
        "timestamp": 1,
        "message": {"body": {"text": "hello"}},
    }

    denied_resp = await handler.handle(FakeRequest("POST", payload=payload, remote="198.51.100.10"))
    assert denied_resp.status == 403

    allowed_v4_resp = await handler.handle(FakeRequest("POST", payload=payload, remote="203.0.113.15"))
    assert allowed_v4_resp.status == 200

    allowed_v6_resp = await handler.handle(FakeRequest("POST", payload=payload, remote="2001:db8::1"))
    assert allowed_v6_resp.status == 200

    no_remote_resp = await handler.handle(FakeRequest("POST", payload=payload, remote=""))
    assert no_remote_resp.status == 403

    assert calls == ["handled", "handled"]


@pytest.mark.asyncio
async def test_webhook_handler_single_ip_allowlist_value() -> None:
    router = Router()
    calls: List[str] = []

    @router.message()
    async def on_message(update: Any) -> None:
        calls.append("handled")

    handler = WebhookHandler(router, allowed_ip_networks=["203.0.113.55"])

    class FakeRequest:
        def __init__(self, method: str, payload: Dict[str, Any], remote: str) -> None:
            self.method = method
            self._payload = payload
            self.headers: Dict[str, str] = {}
            self.remote = remote

        async def json(self) -> Dict[str, Any]:
            return self._payload

    payload = {
        "update_type": "message_created",
        "timestamp": 1,
        "message": {"body": {"text": "hello"}},
    }

    allowed_resp = await handler.handle(FakeRequest("POST", payload=payload, remote="203.0.113.55"))
    assert allowed_resp.status == 200

    denied_resp = await handler.handle(FakeRequest("POST", payload=payload, remote="203.0.113.56"))
    assert denied_resp.status == 403

    assert calls == ["handled"]


def test_webhook_handler_invalid_ip_network_value_raises() -> None:
    with pytest.raises(ValueError):
        WebhookHandler(Router(), allowed_ip_networks=["invalid-network"])


def test_create_webhook_app_registers_route_and_handler() -> None:
    router = Router()
    app = create_webhook_app(
        router=router,
        path="/webhook",
        secret="secret",
        allowed_ip_networks=["203.0.113.0/24"],
    )

    assert WEBHOOK_HANDLER_APP_KEY in app
    assert isinstance(app[WEBHOOK_HANDLER_APP_KEY], WebhookHandler)

    post_paths: List[str] = []
    for route in app.router.routes():
        info = route.get_info()
        route_path = str(info.get("path") or info.get("formatter") or "")
        if route.method == "POST":
            post_paths.append(route_path)

    assert "/webhook" in post_paths


def test_create_https_ssl_context_uses_cert_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    class DummyContext:
        def load_cert_chain(self, cert_path: str, key_path: str) -> None:
            calls["cert_path"] = cert_path
            calls["key_path"] = key_path

    dummy_context = DummyContext()

    def fake_create_default_context(purpose: Any) -> Any:
        calls["purpose"] = purpose
        return dummy_context

    monkeypatch.setattr(
        "maxpybot.dispatcher.webhook.ssl.create_default_context",
        fake_create_default_context,
    )

    result = create_https_ssl_context("cert.pem", "key.pem")

    assert result is dummy_context
    assert calls["purpose"] == ssl.Purpose.CLIENT_AUTH
    assert calls["cert_path"] == "cert.pem"
    assert calls["key_path"] == "key.pem"


@pytest.mark.asyncio
async def test_webhook_handler_retries_processing_and_updates_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    router = Router()
    calls: List[str] = []

    @router.message()
    async def on_message(update: Any) -> None:
        calls.append("handled")

    metrics = WebhookMetrics()
    handler = WebhookHandler(router, max_processing_retries=1, metrics=metrics)

    parse_calls: Dict[str, int] = {"count": 0}

    def flaky_parse_update(payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        parse_calls["count"] += 1
        if parse_calls["count"] == 1:
            raise RuntimeError("temporary parse error")
        return payload

    monkeypatch.setattr(handler._parser, "parse_update", flaky_parse_update)

    class FakeRequest:
        method = "POST"
        headers: Dict[str, str] = {}
        remote = "203.0.113.10"

        async def json(self) -> Dict[str, Any]:
            return {
                "update_type": "message_created",
                "timestamp": 1,
                "message": {"body": {"text": "hello"}},
            }

    response = await handler.handle(FakeRequest())

    assert response.status == 200
    assert parse_calls["count"] == 2
    assert calls == ["handled"]
    assert metrics.requests_total == 1
    assert metrics.retried_total == 1
    assert metrics.processed_total == 1
    assert metrics.failed_total == 0


@pytest.mark.asyncio
async def test_webhook_handler_returns_500_after_retry_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    router = Router()
    metrics = WebhookMetrics()
    handler = WebhookHandler(router, max_processing_retries=2, metrics=metrics)

    def always_fail_parse_update(payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("permanent parse error")

    monkeypatch.setattr(handler._parser, "parse_update", always_fail_parse_update)

    class FakeRequest:
        method = "POST"
        headers: Dict[str, str] = {}
        remote = "203.0.113.10"

        async def json(self) -> Dict[str, Any]:
            return {
                "update_type": "message_created",
                "timestamp": 1,
                "message": {"body": {"text": "hello"}},
            }

    response = await handler.handle(FakeRequest())

    assert response.status == 500
    assert metrics.requests_total == 1
    assert metrics.retried_total == 2
    assert metrics.failed_total == 1
    assert metrics.processed_total == 0


@pytest.mark.asyncio
async def test_webhook_handler_metrics_for_secret_and_ip_rejection() -> None:
    router = Router()
    metrics = WebhookMetrics()
    handler = WebhookHandler(
        router,
        secret="valid-secret",
        allowed_ip_networks=["203.0.113.0/24"],
        metrics=metrics,
    )

    class FakeRequest:
        def __init__(self, headers: Dict[str, str], remote: str) -> None:
            self.method = "POST"
            self.headers = headers
            self.remote = remote

        async def json(self) -> Dict[str, Any]:
            return {
                "update_type": "message_created",
                "timestamp": 1,
                "message": {"body": {"text": "hello"}},
            }

    wrong_secret_resp = await handler.handle(
        FakeRequest(
            headers={WEBHOOK_SECRET_HEADER: "wrong-secret"},
            remote="203.0.113.10",
        )
    )
    assert wrong_secret_resp.status == 403

    wrong_ip_resp = await handler.handle(
        FakeRequest(
            headers={WEBHOOK_SECRET_HEADER: "valid-secret"},
            remote="198.51.100.10",
        )
    )
    assert wrong_ip_resp.status == 403

    assert metrics.requests_total == 2
    assert metrics.rejected_secret_total == 1
    assert metrics.rejected_ip_total == 1
