import pytest

from maxpybot.types import Callback


@pytest.mark.asyncio
async def test_callback_answer_uses_callback_id_and_builds_payload() -> None:
    cb = Callback.model_validate(
        {
            "timestamp": 1,
            "callback_id": "cb-1",
            "payload": "p",
            "user": {
                "user_id": "1",
                "username": "u",
                "first_name": "F",
                "last_name": "L",
                "is_bot": False,
                "last_activity_time": 0,
            },
        }
    )

    calls = {}

    class DummyMessages:
        async def answer_on_callback(self, callback_id: str, callback):  # noqa: ANN001
            calls["callback_id"] = callback_id
            calls["callback"] = callback
            return {"success": True}

    class DummyBot:
        messages = DummyMessages()

    cb.bot = DummyBot()  # type: ignore[assignment]
    result = await cb.answer(notification="ok")

    assert result == {"success": True}
    assert calls["callback_id"] == "cb-1"
    assert calls["callback"] == {"notification": "ok"}


@pytest.mark.asyncio
async def test_callback_answer_rejects_empty_notification() -> None:
    cb = Callback.model_validate(
        {
            "timestamp": 1,
            "callback_id": "cb-1",
            "user": {
                "user_id": "1",
                "username": "u",
                "first_name": "F",
                "last_name": "L",
                "is_bot": False,
                "last_activity_time": 0,
            },
        }
    )

    class DummyMessages:
        async def answer_on_callback(self, callback_id: str, callback):  # noqa: ANN001
            raise AssertionError("should not be called")

    class DummyBot:
        messages = DummyMessages()

    cb.bot = DummyBot()  # type: ignore[assignment]
    with pytest.raises(ValueError, match="notification is empty"):
        await cb.answer(notification="  ")

