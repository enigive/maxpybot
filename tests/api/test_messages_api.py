import pytest
from maxpybot import MaxBot
from maxpybot.types import NewMessageSchema, CallbackAnswerSchema

class DummyTransport:
    def __init__(self):
        self.calls = []
        self.max_retries = 1
    async def request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"ok": True}

@pytest.mark.asyncio
async def test_messages_api_get_messages() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    await bot.messages.get_messages(chat_id=123, message_ids=["m1"], from_marker=1)
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[0][2]["params"] == {"chat_id": 123, "message_ids": "m1", "from": 1}

@pytest.mark.asyncio
async def test_messages_api_send_message() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    body = {"text": "hello", "attachments": [], "link": {}}
    await bot.messages.send_message(body, chat_id=123)
    assert dummy.calls[0][0] == "POST"
    assert dummy.calls[0][1] == "messages"
    assert dummy.calls[0][2]["params"] == {"chat_id": 123}

@pytest.mark.asyncio
async def test_messages_api_edit_message() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    body = {"text": "edited", "attachments": [], "link": {}}
    await bot.messages.edit_message("m1", body)
    assert dummy.calls[0][0] == "PUT"
    assert dummy.calls[0][2]["params"] == {"message_id": "m1"}

@pytest.mark.asyncio
async def test_messages_api_delete_message() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    await bot.messages.delete_message("m1")
    assert dummy.calls[0][0] == "DELETE"
    assert dummy.calls[0][2]["params"] == {"message_id": "m1"}

@pytest.mark.asyncio
async def test_messages_api_get_message_by_id() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    await bot.messages.get_message_by_id("m1")
    assert dummy.calls[0][1] == "messages/m1"

@pytest.mark.asyncio
async def test_messages_api_get_video_details() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    await bot.messages.get_video_attachment_details("v1")
    assert dummy.calls[0][1] == "videos/v1"

@pytest.mark.asyncio
async def test_messages_api_answer_callback() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.messages._transport = dummy  # type: ignore[assignment]
    await bot.messages.answer_on_callback("c1", {"notification": "ok"})
    assert dummy.calls[0][0] == "POST"
    assert dummy.calls[0][1] == "answers"
    assert dummy.calls[0][2]["params"] == {"callback_id": "c1"}
