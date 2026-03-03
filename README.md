# maxpybot

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Асинхронный Python-фреймворк для создания ботов в мессенджере MAX. Разработан с упором на стабильность публичного API, минимализм и удобство, вдохновленное aiogram.

## Основные возможности

- **Asyncio & aiohttp**: Полностью асинхронная архитектура.
- **Стабильный API**: Слой совместимости (`compat/`) защищает ваш код от изменений в MAX API.
- **Типизация**: Строгая типизация с использованием Pydantic v2.
- **Dispatcher & Router**: Гибкая система роутинга событий и мощные фильтры.
- **FSM**: Встроенная машина состояний (Finite State Machine) с поддержкой Memory и Redis.
- **Поддержка Python 3.8+**: Работает на стабильных версиях Python.

## Установка

```bash
pip install maxpybot
```

Для использования Redis в FSM:
```bash
pip install "maxpybot[redis]"
```

## Быстрый старт (Polling)

Самый простой способ запустить бота — использовать Long Polling.

```python
import asyncio
from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher, Router, F
from maxpybot.types import Message

# Инициализация бота и диспетчера
bot = MaxBot("YOUR_BOT_TOKEN")
dp = Dispatcher()
router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот на maxpybot 🚀")

@router.message(F.text)
async def echo_message(message: Message):
    # message.body.text содержит текст сообщения
    await message.answer(f"Вы написали: {message.body.text}")

async def main():
    dp.include_router(router)
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## Работа с Webhooks

Для высоконагруженных ботов рекомендуется использовать Webhooks. `maxpybot` предоставляет встроенную поддержку серверов на базе `aiohttp`.

```python
import asyncio
from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher, Router
from maxpybot.types import Message

bot = MaxBot("YOUR_BOT_TOKEN")
dp = Dispatcher()
router = Router()

@router.message()
async def handle_any(message: Message):
    await message.answer("Получено через Webhook!")

async def main():
    dp.include_router(router)
    # Запуск вебхука (внутри использует aiohttp.web)
    dp.start_webhook(
        bot=bot,
        path="/webhook",
        host="0.0.0.0",
        port=8080,
        secret="SUPER_SECRET_TOKEN"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Машина состояний (FSM)

Управляйте сложными диалогами с помощью состояний.

```python
from maxpybot.fsm import FSMContext, MemoryStorage
from maxpybot.dispatcher import Dispatcher, F, Router
from maxpybot.types import Message

# Для FSM нужно указать хранилище (по умолчанию MemoryStorage)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

@router.message(F.text == "/feedback")
async def start_feedback(message: Message, fsm: FSMContext):
    await fsm.set_state("waiting_for_name")
    await message.answer("Как вас зовут?")

@router.message(state="waiting_for_name")
async def process_name(message: Message, fsm: FSMContext):
    await fsm.update_data(name=message.body.text)
    await fsm.set_state("waiting_for_comment")
    await message.answer(f"Приятно познакомиться, {message.body.text}! Что вы думаете о нас?")

@router.message(state="waiting_for_comment")
async def process_comment(message: Message, fsm: FSMContext):
    data = await fsm.get_data()
    await message.answer(f"Спасибо за отзыв, {data['name']}!")
    await fsm.clear()
```

## Клавиатуры

`maxpybot` поддерживает как Inline, так и Reply клавиатуры.

```python
from maxpybot.types import InlineKeyboard, InlineCallbackButton

# Создание клавиатуры через список строк
kb = InlineKeyboard(buttons=[
    [InlineCallbackButton(text="Нажми меня", payload="btn_pressed")]
])

# Или через хелпер row
kb = InlineKeyboard.from_rows(
    InlineKeyboard.row(InlineCallbackButton(text="Кнопка 1", payload="1")),
    InlineKeyboard.row(InlineCallbackButton(text="Кнопка 2", payload="2"))
)

await message.answer("Выберите опцию:", inline_keyboard=kb)
```

## Документация и примеры

- [Примеры кода](examples/) — готовые примеры для разных сценариев.
- [Руководство по отправке сообщений](docs/sending-messages.md)
- [Webhook и подписки](docs/webhook-and-subscriptions.md)
- [Миграция](MIGRATION.md)

## Разработка

Если вы хотите внести вклад в развитие библиотеки:

1. Клонируйте репозиторий.
2. Установите зависимости для разработки: `pip install -e ".[dev]"`.
3. Запустите тесты: `pytest`.

Библиотека придерживается строгих правил совместимости с MAX API. Все изменения в API мессенджера нормализуются в слое `compat/`, чтобы ваш код продолжал работать без правок.

## Лицензия

Проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).
