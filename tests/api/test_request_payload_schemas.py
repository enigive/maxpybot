from typing import Any, Dict, Optional

import pytest

from maxpybot.api.bots import BotsAPI
from maxpybot.api.chats import ChatsAPI
from maxpybot.api.messages import MessagesAPI
from maxpybot.api.subscriptions import SubscriptionsAPI
from maxpybot.types import (
    BotPatchSchema,
    CallbackAnswerSchema,
    ChatAdminsSchema,
    NewMessageSchema,
    PinMessageSchema,
    UserIdsSchema,
)
from maxpybot.types.generated.models import AttachmentRequest, ChatAdmin


class DummyTransport:
    version = "1.2.5"


def _bind_capture_request_model(api: Any) -> Dict[str, Any]:
    captured: Dict[str, Any] = {}

    async def fake_request_model(  # noqa: ANN202
        model_name: str,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        authorized: bool = True,
        expected_statuses: Any = (200,),
    ) -> Dict[str, Any]:
        captured["model_name"] = model_name
        captured["method"] = method
        captured["path"] = path
        captured["params"] = params
        captured["json_body"] = json_body
        captured["authorized"] = authorized
        captured["expected_statuses"] = expected_statuses
        return captured

    api._request_model = fake_request_model  # type: ignore[method-assign]
    return captured


@pytest.mark.asyncio
async def test_bots_edit_my_info_accepts_schema_and_dict() -> None:
    api = BotsAPI(DummyTransport())  # type: ignore[arg-type]
    captured = _bind_capture_request_model(api)

    await api.edit_my_info(BotPatchSchema(first_name="Max"))
    assert captured["json_body"] == {"first_name": "Max"}

    await api.edit_my_info({"description": "bot"})
    assert captured["json_body"] == {"description": "bot"}


@pytest.mark.asyncio
async def test_chats_request_methods_accept_schema_payloads() -> None:
    api = ChatsAPI(DummyTransport())  # type: ignore[arg-type]
    captured = _bind_capture_request_model(api)

    await api.send_action(chat_id=100, action="typing_on")
    assert captured["json_body"] == {"action": "typing_on"}

    await api.pin_message(chat_id=100, body=PinMessageSchema(message_id="m-1"))
    assert captured["json_body"] == {"message_id": "m-1"}

    await api.post_admins(
        chat_id=100,
        admins=ChatAdminsSchema(admins=[ChatAdmin(user_id=1, permissions=[])]),
    )
    assert captured["json_body"] == {"admins": [{"permissions": [], "user_id": 1}]}

    await api.add_members(chat_id=100, users_body=UserIdsSchema(user_ids=[1, 2]))
    assert captured["json_body"] == {"user_ids": [1, 2]}


@pytest.mark.asyncio
async def test_messages_request_methods_accept_schema_payloads() -> None:
    api = MessagesAPI(DummyTransport())  # type: ignore[arg-type]
    captured = _bind_capture_request_model(api)

    body = NewMessageSchema(
        attachments=[AttachmentRequest(type="image")],
        link={},
        text="hello",
    )

    await api.send_message(body=body, chat_id=200)
    assert captured["params"] == {"chat_id": 200}
    assert captured["json_body"] == {
        "attachments": [{"type": "image"}],
        "link": {},
        "text": "hello",
    }

    await api.edit_message(message_id="m-2", body=body)
    assert captured["params"] == {"message_id": "m-2"}
    assert captured["json_body"] == {
        "attachments": [{"type": "image"}],
        "link": {},
        "text": "hello",
    }

    await api.answer_on_callback(
        callback_id="cb-1",
        callback=CallbackAnswerSchema(notification="ok"),
    )
    assert captured["json_body"] == {"notification": "ok"}


@pytest.mark.asyncio
async def test_subscriptions_subscribe_uses_subscription_schema() -> None:
    api = SubscriptionsAPI(DummyTransport())  # type: ignore[arg-type]
    captured = _bind_capture_request_model(api)

    await api.subscribe("https://bot.example.com/webhook")
    assert captured["json_body"] == {
        "url": "https://bot.example.com/webhook",
        "secret": "",
        "version": "1.2.5",
    }
