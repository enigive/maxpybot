# Быстрый старт

## Установка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
```

## Создание бота

```python
import asyncio

from maxpybot import MaxBot


async def main() -> None:
    bot = MaxBot("YOUR_BOT_TOKEN")
    async with bot:
        me = await bot.bots.get_my_info()
        print(me)


asyncio.run(main())
```

## Получение апдейтов (long polling)

```python
import asyncio

from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher, F
from maxpybot.dispatcher.router import Router
from maxpybot.types import Message


async def main() -> None:
    bot = MaxBot("YOUR_BOT_TOKEN")
    dp = Dispatcher()

    text_router = Router()
    media_router = Router()

    @text_router.message(F.text)
    async def on_text(message: Message) -> None:
        print("Text:", message.body.text)

    @media_router.message(F.body.sticker)
    async def on_sticker(message: Message) -> None:
        print("Sticker in chat:", message.chat.chat_id)

    @media_router.message(F.body.video)
    async def on_video(message: Message) -> None:
        print("Video in chat:", message.chat.chat_id)

    dp.include_routers(text_router, media_router)

    await dp.start_polling(bot)


asyncio.run(main())
```

## Отправка сообщения

```python
import asyncio

from maxpybot import MaxBot


async def main() -> None:
    bot = MaxBot("YOUR_BOT_TOKEN")
    async with bot:
        await bot.send_message(chat_id=1234567890, text="hello from maxpybot")


asyncio.run(main())
```

Дальше: отправка сообщений без JSON (фото/видео/файлы, клавиатуры, форматирование) — `docs/sending-messages.md`.
