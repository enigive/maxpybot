from typing import Any, Dict, List

import pytest
from aiohttp import web

from maxpybot import MaxBot
from maxpybot.dispatcher.router import Router
from maxpybot.exceptions import TimeoutError


@pytest.mark.asyncio
async def test_get_updates_timeout_returns_empty_page() -> None:
    api = MaxBot("token")

    class DummyTransport:
        async def request_json(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise TimeoutError("GET updates", "request timeout exceeded")

    api._transport = DummyTransport()  # type: ignore[assignment]
    response = await api.get_updates(marker=123, timeout_seconds=1, limit=1)

    assert response == {"updates": [], "marker": 123}


@pytest.mark.asyncio
async def test_iter_updates_yields_parsed_updates() -> None:
    api = MaxBot("token", pause_seconds=0)
    pages: List[Dict[str, Any]] = [
        {
            "updates": [
                {
                    "update_type": "message_created",
                    "timestamp": 1,
                    "message": {
                        "sender": {"user_id": 1, "name": "Alice"},
                        "recipient": {"chat_id": 2, "chat_type": "chat", "user_id": 0},
                        "timestamp": 1,
                        "body": {"mid": "m", "seq": 1, "text": "hello"},
                    },
                }
            ],
            "marker": 2,
        },
        {"updates": [], "marker": 2},
    ]

    class DummyTransport:
        def __init__(self) -> None:
            self.calls = 0

        async def request_json(self, *args, **kwargs):  # noqa: ANN002, ANN003
            response = pages[self.calls]
            self.calls += 1
            return response

    dummy = DummyTransport()
    api._transport = dummy  # type: ignore[assignment]

    updates = []
    async for update in api.iter_updates(marker=1):
        updates.append(update)
        break

    assert len(updates) == 1


@pytest.mark.asyncio
async def test_maxbot_start_polling_uses_polling_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    class DummyRunner:
        def __init__(self, api: Any, router: Any) -> None:
            calls["api"] = api
            calls["router"] = router

        async def run(self, marker=None, types=None):  # noqa: ANN001
            calls["marker"] = marker
            calls["types"] = types

    class DummyTransport:
        async def open(self) -> None:
            calls["opened"] = True

        async def close(self) -> None:
            calls["closed"] = True

    monkeypatch.setattr("maxpybot.dispatcher.polling.PollingRunner", DummyRunner)

    bot = MaxBot("token")
    bot._transport = DummyTransport()  # type: ignore[assignment]
    router = Router()

    await bot.start_polling(router=router, marker=10, types=["message_created"])

    assert calls["api"] is bot
    assert calls["router"] is router
    assert calls["marker"] == 10
    assert calls["types"] == ["message_created"]
    assert calls["opened"] is True
    assert calls["closed"] is True


@pytest.mark.asyncio
async def test_maxbot_webhook_subscription_helpers() -> None:
    calls: Dict[str, Any] = {}

    class DummySubscriptions:
        async def subscribe(self, subscribe_url: str, update_types=None, secret: str = ""):  # noqa: ANN001
            calls["subscribe"] = (subscribe_url, update_types, secret)
            return "subscribed"

        async def unsubscribe(self, subscription_url: str) -> str:
            calls["unsubscribe"] = subscription_url
            return "unsubscribed"

        async def unsubscribe_all(self) -> List[str]:
            calls["unsubscribe_all"] = True
            return ["all"]

    bot = MaxBot("token")
    bot.subscriptions = DummySubscriptions()  # type: ignore[assignment]

    subscribed = await bot.subscribe_webhook(
        subscribe_url="https://bot.example.com/webhook",
        update_types=["message_created"],
        secret="s",
    )
    unsubscribed = await bot.unsubscribe_webhook("https://bot.example.com/webhook")
    removed_all = await bot.unsubscribe_all_webhooks()

    assert subscribed == "subscribed"
    assert unsubscribed == "unsubscribed"
    assert removed_all == ["all"]
    assert calls["subscribe"] == ("https://bot.example.com/webhook", ["message_created"], "s")
    assert calls["unsubscribe"] == "https://bot.example.com/webhook"
    assert calls["unsubscribe_all"] is True


def test_maxbot_start_webhook_runs_app(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MaxBot("token")
    router = Router()
    app = web.Application()
    startup_count_before = len(app.on_startup)
    cleanup_count_before = len(app.on_cleanup)
    calls: Dict[str, Any] = {}

    def fake_create_webhook_app(  # noqa: PLR0913
        router: Router,
        path: str,
        secret: str = "",
        secret_header: str = "",
        allowed_ip_networks=None,  # noqa: ANN001
        max_processing_retries: int = 0,
        metrics=None,  # noqa: ANN001
    ) -> web.Application:
        calls["create"] = {
            "router": router,
            "path": path,
            "secret": secret,
            "secret_header": secret_header,
            "allowed_ip_networks": allowed_ip_networks,
            "max_processing_retries": max_processing_retries,
            "metrics": metrics,
        }
        return app

    def fake_ssl_context(cert_path: str, key_path: str) -> str:
        calls["ssl"] = (cert_path, key_path)
        return "ssl-context"

    def fake_run_app(app_obj: web.Application, host: str, port: int, ssl_context: Any) -> None:
        calls["run"] = (app_obj, host, port, ssl_context)

    monkeypatch.setattr(bot, "create_webhook_app", fake_create_webhook_app)
    monkeypatch.setattr("maxpybot.dispatcher.webhook.create_https_ssl_context", fake_ssl_context)
    monkeypatch.setattr("aiohttp.web.run_app", fake_run_app)

    bot.start_webhook(
        router=router,
        path="/webhook",
        host="127.0.0.1",
        port=8443,
        cert_path="cert.pem",
        key_path="key.pem",
        secret="secret",
        subscribe_url="https://bot.example.com/webhook",
        update_types=["message_created"],
        unsubscribe_on_shutdown=True,
    )

    assert calls["create"]["router"] is router
    assert calls["create"]["path"] == "/webhook"
    assert calls["create"]["secret"] == "secret"
    assert calls["ssl"] == ("cert.pem", "key.pem")
    assert calls["run"] == (app, "127.0.0.1", 8443, "ssl-context")
    assert len(app.on_startup) == startup_count_before + 1
    assert len(app.on_cleanup) == cleanup_count_before + 1
