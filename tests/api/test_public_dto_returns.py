from typing import Any, Dict, Optional, Tuple

import pytest

from maxpybot.api.chats import ChatsAPI
from maxpybot.api.messages import MessagesAPI
from maxpybot.types import Chat, Message


class DummyTransport:
    version = "1.2.5"
    max_retries = 1

    async def request_json(  # noqa: PLR0913
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Tuple[int, ...] = (200,),
    ) -> Dict[str, Any]:
        if method == "GET" and path == "chats/200":
            return {
                "chat_id": 200,
                "description": "Chat",
                "icon": {},
                "is_public": False,
                "last_event_time": 1710000000,
                "participants_count": 2,
                "status": "active",
                "title": "General",
                "type": "chat",
            }

        if method == "GET" and path == "messages/m-1":
            return {
                "body": {"mid": "m-1", "seq": 1, "text": "hello", "attachments": []},
                "recipient": {"chat_id": 200, "chat_type": "chat", "user_id": 0},
                "timestamp": 1710000000,
            }

        return {}


@pytest.mark.asyncio
async def test_chats_api_returns_public_chat_dto() -> None:
    api = ChatsAPI(DummyTransport())  # type: ignore[arg-type]
    result = await api.get_chat(200)

    assert isinstance(result, Chat)
    assert result.__class__ is Chat


@pytest.mark.asyncio
async def test_messages_api_returns_public_message_dto() -> None:
    api = MessagesAPI(DummyTransport())  # type: ignore[arg-type]
    result = await api.get_message_by_id("m-1")

    assert isinstance(result, Message)
    assert result.__class__ is Message
