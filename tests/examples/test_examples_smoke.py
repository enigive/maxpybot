import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _load_example_module(name: str) -> ModuleType:
    module_path = EXAMPLES_DIR / "{0}.py".format(name)
    spec = importlib.util.spec_from_file_location("smoke_{0}".format(name), module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load example module: {0}".format(name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_polling_basic_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("polling_basic")

    async def fake_start_polling(self: Any, bot: Any, marker: Any = None, types: Any = None) -> None:
        return None

    monkeypatch.setattr("maxpybot.dispatcher.dispatcher.Dispatcher.start_polling", fake_start_polling)
    await module.main()


@pytest.mark.asyncio
async def test_fsm_feedback_flow_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("fsm_feedback_flow")

    async def fake_start_polling(self: Any, router: Any, marker: Any = None, types: Any = None) -> None:
        return None

    monkeypatch.setattr("maxpybot.api_client.MaxBot.start_polling", fake_start_polling)
    await module.main()


@pytest.mark.asyncio
async def test_api_groups_overview_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("api_groups_overview")

    async def fake_enter(self: Any) -> Any:
        return self

    async def fake_exit(self: Any, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def fake_get_my_info(self: Any) -> Any:
        return {"user_id": "1"}

    async def fake_get_chats(self: Any, count: int = 20, marker: Any = None) -> Any:
        return {"chats": [], "marker": marker}

    async def fake_get_messages(self: Any, **kwargs: Any) -> Any:
        return {"messages": []}

    async def fake_get_subscriptions(self: Any) -> Any:
        return {"subscriptions": []}

    async def fake_get_upload_url(self: Any, upload_type: str) -> Any:
        return {"url": "https://upload.example.com", "token": "t"}

    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aenter__", fake_enter)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aexit__", fake_exit)
    monkeypatch.setattr("maxpybot.api.bots.BotsAPI.get_my_info", fake_get_my_info)
    monkeypatch.setattr("maxpybot.api.chats.ChatsAPI.get_chats", fake_get_chats)
    monkeypatch.setattr("maxpybot.api.messages.MessagesAPI.get_messages", fake_get_messages)
    monkeypatch.setattr("maxpybot.api.subscriptions.SubscriptionsAPI.get_subscriptions", fake_get_subscriptions)
    monkeypatch.setattr("maxpybot.api.uploads.UploadsAPI.get_upload_url", fake_get_upload_url)

    await module.main()


@pytest.mark.asyncio
async def test_subscriptions_manage_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("subscriptions_manage")

    async def fake_enter(self: Any) -> Any:
        return self

    async def fake_exit(self: Any, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def fake_subscribe_webhook(self: Any, subscribe_url: str, update_types: Any = None, secret: str = "") -> Any:
        return {"success": True, "url": subscribe_url, "types": update_types, "secret": secret}

    async def fake_unsubscribe_webhook(self: Any, subscription_url: str) -> Any:
        return {"success": True, "url": subscription_url}

    async def fake_unsubscribe_all(self: Any) -> Any:
        return [{"success": True}]

    async def fake_get_subscriptions(self: Any) -> Any:
        return {"subscriptions": []}

    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aenter__", fake_enter)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aexit__", fake_exit)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.subscribe_webhook", fake_subscribe_webhook)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.unsubscribe_webhook", fake_unsubscribe_webhook)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.unsubscribe_all_webhooks", fake_unsubscribe_all)
    monkeypatch.setattr("maxpybot.api.subscriptions.SubscriptionsAPI.get_subscriptions", fake_get_subscriptions)

    await module.main()


@pytest.mark.asyncio
async def test_uploads_basic_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("uploads_basic")

    async def fake_enter(self: Any) -> Any:
        return self

    async def fake_exit(self: Any, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def fake_upload_from_file(self: Any, upload_type: str, file_path: str) -> Any:
        return {"token": "file-token", "upload_type": upload_type, "file_path": file_path}

    async def fake_upload_from_url(self: Any, upload_type: str, url: str) -> Any:
        return {"token": "url-token", "upload_type": upload_type, "url": url}

    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aenter__", fake_enter)
    monkeypatch.setattr("maxpybot.api_client.MaxBot.__aexit__", fake_exit)
    monkeypatch.setattr("maxpybot.api.uploads.UploadsAPI.upload_media_from_file", fake_upload_from_file)
    monkeypatch.setattr("maxpybot.api.uploads.UploadsAPI.upload_media_from_url", fake_upload_from_url)

    await module.main()


def test_webhook_https_server_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_example_module("webhook_https_server")

    def fake_start_webhook(self: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr("maxpybot.api_client.MaxBot.start_webhook", fake_start_webhook)
    module.main()
