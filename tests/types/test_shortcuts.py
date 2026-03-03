import pytest
from unittest.mock import AsyncMock, MagicMock
from maxpybot.api_client import MaxBot
from maxpybot.compat.update_parser import UpdateParser
from maxpybot.types.models import Message, Callback, Recipient

@pytest.mark.asyncio
async def test_bot_injection_and_shortcuts():
    bot = MagicMock(spec=MaxBot)
    bot.send_message = AsyncMock()
    bot.messages = MagicMock()
    bot.messages.answer_on_callback = AsyncMock()
    
    parser = UpdateParser()
    
    # Test Message shortcut
    raw_message_update = {
        "update_type": "message_created",
        "timestamp": 123456789,
        "message": {
            "mid": "msg123",
            "recipient": {"chat_id": 111, "chat_type": "group", "user_id": 0},
            "body": {"text": "hello", "attachments": [], "mid": "msg123", "seq": 1},
            "timestamp": 123456789
        }
    }
    
    update = parser.parse_update(raw_message_update, bot=bot)
    message = update.message
    
    print(f"Update type: {type(update)}")
    print(f"Message type: {type(message)}")
    
    assert message.bot == bot
    
    await message.answer(text="reply")
    bot.send_message.assert_called_once_with(
        chat_id=111,
        text="reply",
        notify=True,
        format=None,
        reply_to_message_id=None,
        forward_message_id=None,
        inline_keyboard=None,
        reply_keyboard=None
    )

@pytest.mark.asyncio
async def test_callback_shortcut():
    bot = MagicMock(spec=MaxBot)
    bot.messages = MagicMock()
    bot.messages.answer_on_callback = AsyncMock()
    
    parser = UpdateParser()
    
    # Test Callback shortcut
    raw_callback_update = {
        "update_type": "message_callback",
        "timestamp": 123456789,
        "callback": {
            "callback_id": "cb123",
            "user": {
                "user_id": "222",
                "name": "User",
                "first_name": "U",
                "last_name": "S",
                "username": "user",
                "is_bot": False,
                "last_activity_time": 0
            },
            "payload": "btn_click",
            "timestamp": 123456789
        },
        "message": {
            "mid": "msg123",
            "recipient": {"chat_id": 111, "chat_type": "group", "user_id": 0},
            "body": {"text": "hello", "attachments": [], "mid": "msg123", "seq": 1},
            "timestamp": 123456789
        }
    }
    
    update = parser.parse_update(raw_callback_update, bot=bot)
    callback = update.callback
    
    print(f"Update type: {type(update)}")
    print(f"Callback type: {type(callback)}")
    
    assert callback.bot == bot
    
    await callback.answer(notification="ok")
    bot.messages.answer_on_callback.assert_called_once_with(
        callback_id="cb123",
        callback={"notification": "ok"}
    )
