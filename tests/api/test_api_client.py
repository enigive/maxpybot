from typing import Any, Dict, List

import pytest

from maxpybot.api_client import MaxBotAPI
from maxpybot.exceptions import TimeoutError


@pytest.mark.asyncio
async def test_get_updates_timeout_returns_empty_page() -> None:
    api = MaxBotAPI("token")

    class DummyTransport:
        async def request_json(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise TimeoutError("GET updates", "request timeout exceeded")

    api._transport = DummyTransport()  # type: ignore[attr-defined]
    response = await api.get_updates(marker=123, timeout_seconds=1, limit=1)

    assert response == {"updates": [], "marker": 123}


@pytest.mark.asyncio
async def test_iter_updates_yields_parsed_updates() -> None:
    api = MaxBotAPI("token", pause_seconds=0)
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
    api._transport = dummy  # type: ignore[attr-defined]

    updates = []
    async for update in api.iter_updates(marker=1):
        updates.append(update)
        break

    assert len(updates) == 1
