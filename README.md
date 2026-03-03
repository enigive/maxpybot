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
    await message.answer(f"Вы написали: {message.text}")

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
from maxpybot import MaxBot
from maxpybot.dispatcher import Router, create_webhook_app
from aiohttp import web

bot = MaxBot("YOUR_BOT_TOKEN")
router = Router()

@router.message()
async def handle_any(message):
    await message.answer("Получено через Webhook!")

# Создание aiohttp приложения
app = create_webhook_app(
    bot=bot,
    router=router,
    path="/webhook",
    secret="SUPER_SECRET_TOKEN"
)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
```

## Машина состояний (FSM)

Управляйте сложными диалогами с помощью состояний.

```python
from maxpybot.fsm import FSMContext
from maxpybot.dispatcher import F, Router
from maxpybot.types import Message

router = Router()

@router.message(F.text == "/feedback")
async def start_feedback(message: Message, state: FSMContext):
    await state.set_state("waiting_for_name")
    await message.answer("Как вас зовут?")

@router.message(F.state == "waiting_for_name")
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state("waiting_for_comment")
    await message.answer(f"Приятно познакомиться, {message.text}! Что вы думаете о нас?")

@router.message(F.state == "waiting_for_comment")
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(f"Спасибо за отзыв, {data['name']}!")
    await state.clear()
```

## Клавиатуры

`maxpybot` поддерживает как Inline, так и Reply клавиатуры.

```python
from maxpybot.types import InlineKeyboard, InlineCallbackButton

kb = InlineKeyboard(buttons=[
    [InlineCallbackButton(text="Нажми меня", payload="btn_pressed")]
])

await message.answer("Выберите опцию:", reply_markup=kb)
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
