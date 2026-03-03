# Migration guide

Документирует несовместимые изменения и способы миграции.

## 0.x -> 0.x (Typed Dispatcher Redesign)

### 1) `MaxBotAPI` -> `MaxBot`

Старый импорт/класс удален.

Было:

```python
from maxpybot import MaxBotAPI

bot = MaxBotAPI("TOKEN")
```

Стало:

```python
from maxpybot import MaxBot

bot = MaxBot("TOKEN")
```

### 2) Рекомендуемый запуск polling через `Dispatcher`

Было:

```python
from maxpybot.dispatcher.polling import PollingRunner

await PollingRunner(bot, router).run(types=["message_created"])
```

Стало:

```python
from maxpybot.dispatcher import Dispatcher

dp = Dispatcher()
dp.include_router(router)
await dp.start_polling(bot, types=["message_created"])
```

### 3) Typed handlers вместо dict-style

Было:

```python
@router.message()
async def on_message(update):
    text = update["message"]["body"]["text"]
```

Стало:

```python
from maxpybot.types import Message

@router.message()
async def on_message(message: Message):
    text = message.body.text
```

### 4) Явные декораторы update-типов

Было:

```python
@router.on_update("message_created")
async def on_message(update):
    ...
```

Стало:

```python
@router.message_created()
async def on_message(message: Message):
    ...
```

### 5) Deep link payload

- каноничный путь: `BotStartedUpdate.start_payload` (из `bot_started`);
- fallback в сообщении: `Message.start_payload` (из `/start payload`).

## Политика на будущее

- Любой новый breaking change добавляется отдельным разделом в этот файл.
- Перед удалением старого поведения — минимум один этап с предупреждениями/описанием миграции.
