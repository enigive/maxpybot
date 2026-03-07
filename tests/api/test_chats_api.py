import pytest
from maxpybot import MaxBot
from maxpybot.types import ChatPatchSchema, SendActionSchema, PinMessageSchema, ChatAdminsSchema, UserIdsSchema

class DummyTransport:
    def __init__(self):
        self.calls = []
    async def request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"ok": True}

@pytest.mark.asyncio
async def test_chats_api_get_chats() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_chats(count=10, marker=1)
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[0][1] == "chats"
    assert dummy.calls[0][2]["params"] == {"count": 10, "marker": 1}

@pytest.mark.asyncio
async def test_chats_api_get_chat_by_link() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_chat_by_link("@my_chat")
    # quote(safe="@") means @ is NOT encoded
    assert dummy.calls[0][1] == "chats/@my_chat"

@pytest.mark.asyncio
async def test_chats_api_get_chat() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_chat(123)
    assert dummy.calls[0][1] == "chats/123"

@pytest.mark.asyncio
async def test_chats_api_edit_chat() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.edit_chat(123, {"title": "new"})
    assert dummy.calls[0][0] == "PATCH"
    assert dummy.calls[0][2]["json_body"] == {"title": "new"}

@pytest.mark.asyncio
async def test_chats_api_delete_chat() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.delete_chat(123)
    assert dummy.calls[0][0] == "DELETE"

@pytest.mark.asyncio
async def test_chats_api_send_action() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.send_action(123, "typing_on")
    assert dummy.calls[0][0] == "POST"
    assert dummy.calls[0][2]["json_body"] == {"action": "typing_on"}

@pytest.mark.asyncio
async def test_chats_api_pin_unpin() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.pin_message(123, {"message_id": "m1"})
    await bot.chats.unpin_message(123)
    assert dummy.calls[0][0] == "PUT"
    assert dummy.calls[1][0] == "DELETE"

@pytest.mark.asyncio
async def test_chats_api_membership() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_membership(123)
    await bot.chats.leave_chat(123)
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[1][0] == "DELETE"

@pytest.mark.asyncio
async def test_chats_api_admins() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_admins(123)
    await bot.chats.post_admins(123, {"admins": []})
    await bot.chats.delete_admins(123, 456)
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[1][0] == "POST"
    assert dummy.calls[2][0] == "DELETE"

@pytest.mark.asyncio
async def test_chats_api_members() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.chats._transport = dummy  # type: ignore[assignment]
    await bot.chats.get_members(123, user_ids=[1, 2])
    await bot.chats.add_members(123, {"user_ids": [1]})
    await bot.chats.remove_member(123, 1)
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[0][2]["params"]["user_ids"] == "1,2"
    assert dummy.calls[1][0] == "POST"
    assert dummy.calls[2][0] == "DELETE"
