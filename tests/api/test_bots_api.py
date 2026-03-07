import pytest
from maxpybot import MaxBot
from maxpybot.types import BotPatchSchema, BotInfo

class DummyTransport:
    def __init__(self):
        self.calls = []
    async def request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        # Return valid payload for BotInfo
        return {
            "user_id": 123, 
            "name": "test_bot",
            "first_name": "Test",
            "is_bot": True
        }

@pytest.mark.asyncio
async def test_bots_api_get_my_info() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.bots._transport = dummy  # type: ignore[assignment]
    
    info = await bot.bots.get_my_info()
    
    # Check if it's a BotInfo instance or a dict
    if isinstance(info, BotInfo):
        assert info.user_id == 123
        assert info.username == "test_bot"
    else:
        assert info["user_id"] == 123
        assert info["name"] == "test_bot"
        
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[0][1] == "me"

@pytest.mark.asyncio
async def test_bots_api_edit_my_info_dict() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.bots._transport = dummy  # type: ignore[assignment]
    
    patch = {"name": "new_name"}
    info = await bot.bots.edit_my_info(patch)
    
    if isinstance(info, BotInfo):
        assert info.username == "test_bot"
    else:
        assert info["name"] == "test_bot"
        
    assert dummy.calls[0][0] == "PATCH"
    assert dummy.calls[0][1] == "me"
    assert dummy.calls[0][2]["json_body"] == {"name": "new_name"}

@pytest.mark.asyncio
async def test_bots_api_edit_my_info_schema() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.bots._transport = dummy  # type: ignore[assignment]
    
    patch = BotPatchSchema(name="schema_name")
    await bot.bots.edit_my_info(patch)
    
    assert dummy.calls[0][2]["json_body"] == {"name": "schema_name"}

@pytest.mark.asyncio
async def test_bots_api_parity_aliases() -> None:
    bot = MaxBot("token")
    assert bot.bots.getMyInfo == bot.bots.get_my_info
    assert bot.bots.editMyInfo == bot.bots.edit_my_info
