import pytest

from maxpybot.api.subscriptions import SubscriptionsAPI


@pytest.mark.asyncio
async def test_unsubscribe_all_calls_unsubscribe_for_each_url() -> None:
    api = SubscriptionsAPI(transport=None)  # type: ignore[arg-type]
    called_urls = []

    async def fake_get_subscriptions():
        return {
            "subscriptions": [
                {"url": "https://bot.example.com/webhook-a"},
                {"url": "https://bot.example.com/webhook-b"},
            ]
        }

    async def fake_unsubscribe(url: str):
        called_urls.append(url)
        return {"success": True}

    api.get_subscriptions = fake_get_subscriptions  # type: ignore[method-assign]
    api.unsubscribe = fake_unsubscribe  # type: ignore[method-assign]

    result = await api.unsubscribe_all()

    assert called_urls == [
        "https://bot.example.com/webhook-a",
        "https://bot.example.com/webhook-b",
    ]
    assert len(result) == 2
