import pytest
from typing import Any, Dict, Optional
from maxpybot.dispatcher.di import (
    invoke_handler, 
    HandlerSignatureError, 
    _coerce_model,
    _extract_callback,
    _extract_chat_id,
    _extract_user_id
)
from maxpybot.dispatcher.context import HandlerContext
from maxpybot.types import Update, Callback, Message

class MockRouter:
    pass

@pytest.mark.asyncio
async def test_di_resilience_to_validation_failure():
    # Callback schema requires 'callback_id' and 'timestamp' etc.
    update = {
        "update_type": "callback",
        "callback": {
            "callback_id": "cb1",
            # missing 'timestamp' and 'user'
        }
    }
    context = HandlerContext(
        update=update, 
        router=MockRouter(), 
        storage=None, 
        fsm=None, 
        state=None
    )

    async def handler(callback: Callback):
        return callback

    # After fix: incomplete data → model_construct is used → always a typed object
    result = await invoke_handler(handler, context)
    assert isinstance(result, Callback)
    assert result.callback_id == "cb1"

@pytest.mark.asyncio
async def test_di_resilience_to_foreign_model():
    class ForeignCallback:
        def __init__(self, callback_id, timestamp, user):
            self.callback_id = callback_id
            self.timestamp = timestamp
            self.user = user
            self.message = None
        def model_dump(self, **kwargs):
            return {"callback_id": self.callback_id, "timestamp": self.timestamp, "user": self.user}

    foreign_cb = ForeignCallback(callback_id="cb2", timestamp=123, user={"user_id": 1})
    
    update = {
        "update_type": "callback",
        "callback": foreign_cb
    }
    
    context = HandlerContext(
        update=update, 
        router=MockRouter(), 
        storage=None, 
        fsm=None, 
        state=None
    )

    async def handler(callback: Callback):
        return callback

    result = await invoke_handler(handler, context)
    # Foreign object with valid model_dump → coerced to proper Callback
    assert isinstance(result, Callback)
    assert result.callback_id == "cb2"

@pytest.mark.asyncio
async def test_extract_chat_id_from_dict_message():
    update = {
        "update_type": "message",
        "message": {
            "text": "hello",
            "chat": {"chat_id": 123}
        }
    }
    context = HandlerContext(
        update=update, 
        router=MockRouter(), 
        storage=None, 
        fsm=None, 
        state=None
    )
    
    async def handler(chat_id: int):
        return chat_id
        
    result = await invoke_handler(handler, context)
    assert result == 123

@pytest.mark.asyncio
async def test_extract_user_id_from_dict_callback():
    update = {
        "update_type": "callback",
        "callback": {
            "callback_id": "c1",
            "user": {"user_id": 456}
        }
    }
    context = HandlerContext(
        update=update, 
        router=MockRouter(), 
        storage=None, 
        fsm=None, 
        state=None
    )
    
    async def handler(user_id: int):
        return user_id
        
    result = await invoke_handler(handler, context)
    assert result == 456

def test_coerce_model_none():
    assert _coerce_model(None, Callback) is None

def test_coerce_model_foreign_model_dump_fail():
    class BadModel:
        def model_dump(self, **kwargs):
            raise ValueError("fail")
    
    bad = BadModel()
    assert _coerce_model(bad, Callback) is bad

def test_extract_callback_message_injection_to_dict():
    update = {
        "message": {"text": "msg"},
        "callback": {"callback_id": "c"}
    }
    cb = _extract_callback(update)
    assert isinstance(cb, dict)
    assert "message" in cb
    assert cb["message"]["text"] == "msg"

def test_extract_user_id_from_dict_message_sender():
    update = {
        "message": {
            "sender": {"user_id": 789}
        }
    }
    assert _extract_user_id(update) == 789
