# Публичный API (справочник)

Эта страница описывает **публичные точки входа** библиотеки: `MaxBot`, группы API (`bot.messages`, `bot.uploads`, ...), dispatcher, FSM, типы и ошибки.

## 1) Основная точка входа: `MaxBot`

```python
from maxpybot import MaxBot

bot = MaxBot("YOUR_BOT_TOKEN")
```

### Конструктор

`MaxBot(token, ...)` параметры:

- `token: str` — токен бота (**обязателен**)
- `base_url: str` — базовый URL API (по умолчанию `https://platform-api.max.ru/`)
- `version: str` — версия API (по умолчанию `1.2.5`)
- `timeout_seconds: int` — timeout long polling / запросов (по умолчанию `30`)
- `pause_seconds: int` — пауза между пустыми страницами апдейтов (по умолчанию `1`)
- `max_retries: int` — ретраи в transport-слое (по умолчанию `3`)
- `debug: bool` — включает более подробный разбор апдейтов в compat (для диагностики)
- `update_handler: Optional[Callable[[Any], None]]` — если задан, `iter_updates()` будет вызывать handler вместо `yield`
- `session: Any` — внешний `aiohttp.ClientSession` (DI), если хотите управлять жизненным циклом сами

### Жизненный цикл (aiohttp session)

Рекомендуемый стиль — через async context manager:

```python
async with bot:
    me = await bot.bots.get_my_info()
```

### Группы API

У `bot` всегда доступны:

- `bot.bots` — методы профиля бота
- `bot.chats` — методы по чатам
- `bot.messages` — методы по сообщениям и callback
- `bot.subscriptions` — webhook subscriptions
- `bot.uploads` — загрузка медиа

Полный список методов по группам: `docs/api-groups.md`.

### Получение апдейтов

- `await bot.get_updates(marker=None, timeout_seconds=None, limit=None, types=None) -> dict`
- `async for update in bot.iter_updates(marker=None, types=None): ...`
- `await bot.start_polling(router, marker=None, types=None) -> None`

### Webhook

Сборка `aiohttp.web.Application`:

- `bot.create_webhook_app(router, path, secret="", secret_header="X-Max-Bot-Api-Secret", allowed_ip_networks=None, max_processing_retries=0, metrics=None)`

Запуск сервера (helper поверх `aiohttp.web.run_app`):

- `bot.start_webhook(...)`

Управление подписками:

- `await bot.subscribe_webhook(subscribe_url, update_types=None, secret="")`
- `await bot.unsubscribe_webhook(subscription_url)`
- `await bot.unsubscribe_all_webhooks()`

Подробнее: `docs/webhook-and-subscriptions.md`.

### Отправка сообщений (high-level, без JSON)

`MaxBot` предоставляет удобные методы отправки без `body`/dict:

- `await bot.send_message(chat_id=..., text=..., inline_keyboard=..., reply_keyboard=...)`
- `await bot.send_image(chat_id=..., file_path=... | url=... | token=..., caption=..., inline_keyboard=..., reply_keyboard=...)`
- `await bot.send_video(...)`
- `await bot.send_audio(...)`
- `await bot.send_file(...)`
- `await bot.send_sticker(chat_id=..., code=...)`
- `await bot.send_contact(chat_id=..., name=..., contact_id=..., vcf_phone=..., vcf_info=...)`
- `await bot.send_location(chat_id=..., latitude=..., longitude=..., text=..., inline_keyboard=..., reply_keyboard=...)`
- `await bot.send_share(chat_id=..., url=..., text=..., inline_keyboard=..., reply_keyboard=...)`

Практические примеры и типы клавиатур: `docs/sending-messages.md`.

## 2) Dispatcher (`maxpybot.dispatcher`)

Импорты:

```python
from maxpybot.dispatcher import Dispatcher, Router, F
```

Ключевые сущности:

- `Router` — регистрация хендлеров и dispatch апдейтов
- `Dispatcher` — корневой router + удобные include методы
- `F` — магические фильтры (по тексту, вложениям, callback payload и т.д.)
- `PollingRunner` — низкоуровневый запуск polling
- `WebhookHandler` — обработчик webhook запросов
- `WebhookMetrics` — счетчики обработки webhook

Подробнее: `docs/updates-and-dispatcher.md`.

## 3) FSM (`maxpybot.fsm`)

Импорты:

```python
from maxpybot.fsm import FSMContext, MemoryStorage, RedisStorage
```

Ключевые сущности:

- `BaseStorage`, `StorageKey` — интерфейс и ключ хранения состояния
- `FSMContext` — `get_state/set_state/get_data/update_data/clear`
- `MemoryStorage` — in-memory storage
- `RedisStorage` — опциональный адаптер (нужен пакет `redis`)

Подробнее: `docs/fsm-and-storage.md`.

## 4) Типы и схемы (`maxpybot.types`)

Импорт публичных DTO и request-схем:

```python
from maxpybot.types import Message, Chat, User
from maxpybot.types import NewMessageSchema, BotPatchSchema
```

- DTO для ответов и апдейтов: `User`, `Chat`, `Message`, `Update`, `MessageCreatedUpdate`, ...
- Схемы запросов (body/patch): `NewMessageSchema`, `ChatPatchSchema`, ...

Подробнее:

- `docs/types-reference.md` — что за типы и где применяются
- `docs/public-schemas.md` — список request-схем и их назначение

## 5) Отправка сообщений, вложения и клавиатуры

Практический гайд по отправке **без JSON**, включая вложения и клавиатуры:

- `docs/sending-messages.md`

## 6) Ошибки и исключения (`maxpybot.exceptions`)

Публичные исключения:

- `MaxPyBotError` — базовый класс
- `EmptyTokenError` — пустой token
- `InvalidURLError` — некорректный API URL
- `APIError` — ошибка, пришедшая от MAX API (`status_code/message/details`)
- `NetworkError` — ошибки сети/transport
- `TimeoutError` — таймаут запроса
- `SerializationError` — ошибки JSON encode/decode

