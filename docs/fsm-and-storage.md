# FSM и storage

`maxpybot.fsm` добавляет минимальный stateful-слой поверх dispatcher.

## Что доступно

- `StorageKey(chat_id, user_id)` — ключ состояния пользователя в чате.
- `BaseStorage` — интерфейс хранилища состояний.
- `FSMContext` — удобная обертка над storage (`get_state/set_state/get_data/update_data/clear`).
- `MemoryStorage` — встроенный in-memory адаптер.
- `RedisStorage` — опциональный production-адаптер.
- автоматическая инжекция `FSMContext` и `state` через `Router(storage=...)`.

## In-memory пример

```python
from maxpybot.dispatcher.router import Router
from maxpybot.fsm import FSMContext, MemoryStorage
from maxpybot.types import Message

storage = MemoryStorage()
router = Router(storage=storage)

@router.message_created(state="await_name")
async def on_name(message: Message, fsm: FSMContext, state: str) -> None:
    await fsm.update_data(name=message.body.text)
    await fsm.clear()
```

## Redis storage (опционально)

Для `RedisStorage.from_url(...)` нужен пакет `redis`:

```bash
pip install redis
```

Пример:

```python
from maxpybot.fsm import RedisStorage

storage = RedisStorage.from_url(
    "redis://localhost:6379/0",
    key_prefix="my-bot:fsm",
    state_ttl_seconds=3600,
    data_ttl_seconds=3600,
)
```

## Многошаговый сценарий

Готовый пример: `examples/fsm_feedback_flow.py`.
