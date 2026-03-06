from __future__ import annotations

from typing import Any, Dict

import pytest

from maxpybot.dispatcher.router import Router
from maxpybot.types import BotStartedUpdate, Message


@pytest.mark.asyncio
async def test_router_resolves_future_annotations_for_supported_injections() -> None:
    router = Router()
    captured: Dict[str, Any] = {}

    @router.bot_started()
    async def on_started(update: BotStartedUpdate) -> None:
        captured["start_payload"] = update.start_payload

    @router.message_created()
    async def on_message(message: Message) -> None:
        captured["chat_id"] = message.chat.chat_id
        captured["text"] = message.body.text

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
                "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
                "timestamp": 2,
            },
        }
    )

    assert captured == {
        "start_payload": "promo_summer2025",
        "chat_id": 200,
        "text": "hello",
    }
