# Быстрый старт

## Установка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
```

## Создание клиента

```python
import asyncio

from maxpybot import MaxBotAPI


async def main() -> None:
    async with MaxBotAPI("YOUR_BOT_TOKEN") as api:
        me = await api.bots.get_my_info()
        print(me)


asyncio.run(main())
```

## Получение апдейтов (long polling)

```python
import asyncio

from maxpybot import MaxBotAPI


async def main() -> None:
    async with MaxBotAPI("YOUR_BOT_TOKEN") as api:
        async for update in api.iter_updates():
            print(update)


asyncio.run(main())
```

## Отправка сообщения

```python
import asyncio

from maxpybot import MaxBotAPI


async def main() -> None:
    async with MaxBotAPI("YOUR_BOT_TOKEN") as api:
        await api.messages.send_message(
            body={"text": "hello from maxpybot"},
            chat_id=1234567890,
        )


asyncio.run(main())
```
