import pytest
from maxpybot import MaxBot

class DummyTransport:
    def __init__(self):
        self.calls = []
        self.version = "1.2.5"
    async def request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if method == "GET" and path == "subscriptions":
            return {"subscriptions": [{"url": "https://test.com/1"}, {"url": "https://test.com/2"}]}
        return {"ok": True}

@pytest.mark.asyncio
async def test_subscriptions_api_get_subscriptions() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.subscriptions._transport = dummy
    
    res = await bot.subscriptions.get_subscriptions()
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[0][1] == "subscriptions"

@pytest.mark.asyncio
async def test_subscriptions_api_subscribe() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.subscriptions._transport = dummy
    
    await bot.subscriptions.subscribe("https://test.com", update_types=["message_created"], secret="s")
    assert dummy.calls[0][0] == "POST"
    assert dummy.calls[0][1] == "subscriptions"
    assert dummy.calls[0][2]["json_body"]["url"] == "https://test.com"
    assert dummy.calls[0][2]["json_body"]["update_types"] == ["message_created"]
    assert dummy.calls[0][2]["json_body"]["secret"] == "s"

@pytest.mark.asyncio
async def test_subscriptions_api_unsubscribe() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.subscriptions._transport = dummy
    
    await bot.subscriptions.unsubscribe("https://test.com")
    assert dummy.calls[0][0] == "DELETE"
    assert dummy.calls[0][1] == "subscriptions"
    assert dummy.calls[0][2]["params"]["url"] == "https://test.com"

@pytest.mark.asyncio
async def test_subscriptions_api_unsubscribe_all() -> None:
    bot = MaxBot("token")
    dummy = DummyTransport()
    bot.subscriptions._transport = dummy
    
    results = await bot.subscriptions.unsubscribe_all()
    # 1 GET + 2 DELETE
    assert len(dummy.calls) == 3
    assert dummy.calls[0][0] == "GET"
    assert dummy.calls[1][0] == "DELETE"
    assert dummy.calls[1][2]["params"]["url"] == "https://test.com/1"
    assert dummy.calls[2][0] == "DELETE"
    assert dummy.calls[2][2]["params"]["url"] == "https://test.com/2"
    assert len(results) == 2

@pytest.mark.asyncio
async def test_subscriptions_api_parity_aliases() -> None:
    bot = MaxBot("token")
    assert bot.subscriptions.getSubscriptions == bot.subscriptions.get_subscriptions
    assert bot.subscriptions.unsubscribeAll == bot.subscriptions.unsubscribe_all
