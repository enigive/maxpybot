from typing import Any, Dict

from maxpybot.fsm import MemoryStorage, create_fsm_context, create_fsm_context_from_update, resolve_storage_key_from_update


class _ModelLikeUpdate:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, by_alias: bool = False) -> Dict[str, Any]:
        return dict(self._payload)


def test_resolve_storage_key_from_message_update() -> None:
    key = resolve_storage_key_from_update(
        {
            "update_type": "message_created",
            "message": {
                "recipient": {"chat_id": 100},
                "sender": {"user_id": 200},
            },
        }
    )
    assert key is not None
    assert key.chat_id == 100
    assert key.user_id == 200


def test_resolve_storage_key_from_dialog_update_with_user() -> None:
    key = resolve_storage_key_from_update(
        {
            "update_type": "dialog_muted",
            "chat_id": 300,
            "user": {"user_id": "400"},
        }
    )
    assert key is not None
    assert key.chat_id == 300
    assert key.user_id == 400


def test_resolve_storage_key_from_model_like_update() -> None:
    update = _ModelLikeUpdate({"chat_id": 111, "user_id": 222})
    key = resolve_storage_key_from_update(update)
    assert key is not None
    assert key.chat_id == 111
    assert key.user_id == 222


def test_create_context_from_update_returns_none_without_ids() -> None:
    storage = MemoryStorage()
    context = create_fsm_context_from_update(storage=storage, update={"update_type": "message_removed"})
    assert context is None


def test_create_fsm_context_from_explicit_ids() -> None:
    storage = MemoryStorage()
    context = create_fsm_context(storage=storage, chat_id="500", user_id="600")
    assert context.key.chat_id == 500
    assert context.key.user_id == 600
