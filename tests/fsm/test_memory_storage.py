import pytest

from maxpybot.fsm import FSMContext, MemoryStorage, StorageKey


@pytest.mark.asyncio
async def test_memory_storage_state_and_data_lifecycle() -> None:
    storage = MemoryStorage()
    key = StorageKey(chat_id=10, user_id=20)

    assert await storage.get_state(key) is None
    assert await storage.get_data(key) == {}

    await storage.set_state(key, "awaiting_name")
    assert await storage.get_state(key) == "awaiting_name"

    await storage.set_data(key, {"step": 1})
    assert await storage.get_data(key) == {"step": 1}

    updated = await storage.update_data(key, {"name": "Alice"}, finished=False)
    assert updated == {"step": 1, "name": "Alice", "finished": False}

    await storage.clear(key)
    assert await storage.get_state(key) is None
    assert await storage.get_data(key) == {}


@pytest.mark.asyncio
async def test_fsm_context_wraps_memory_storage() -> None:
    storage = MemoryStorage()
    context = FSMContext(storage=storage, key=StorageKey(chat_id=100, user_id=200))

    await context.set_state("awaiting_email")
    await context.update_data(email="alice@example.com")

    assert await context.get_state() == "awaiting_email"
    assert await context.get_data() == {"email": "alice@example.com"}

    await context.clear()
    assert await context.get_state() is None
    assert await context.get_data() == {}
