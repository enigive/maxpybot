# Cookbook

Набор типовых сценариев для быстрого старта.

## 1) Бот поддержки (FSM + маршрутизация)

Когда нужен диалог в несколько шагов (например: имя -> контакт -> тикет).

```python
from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher
from maxpybot.dispatcher.filters import text_contains
from maxpybot.dispatcher.router import Router
from maxpybot.fsm import FSMContext, MemoryStorage
from maxpybot.types import Message

bot = MaxBot("TOKEN")
dp = Dispatcher(storage=MemoryStorage())
router = Router()

STATE_WAIT_NAME = "support:wait_name"
STATE_WAIT_CONTACT = "support:wait_contact"

@router.message_created(text_contains("/support"))
async def start_support(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await fsm.set_state(STATE_WAIT_NAME)
    await bot.messages.send_message(chat_id=message.chat.chat_id, body={"text": "Как вас зовут?"})

@router.message_created(state=STATE_WAIT_NAME)
async def save_name(message: Message, fsm: FSMContext) -> None:
    await fsm.update_data(name=message.body.text)
    await fsm.set_state(STATE_WAIT_CONTACT)
    await bot.messages.send_message(chat_id=message.chat.chat_id, body={"text": "Оставьте контакт"})

@router.message_created(state=STATE_WAIT_CONTACT)
async def finish_support(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    await fsm.clear()
    await bot.messages.send_message(
        chat_id=message.chat.chat_id,
        body={"text": "Спасибо, {0}. Мы свяжемся.".format(data.get("name", "друг"))},
    )

dp.include_router(router)
```

## 2) Модерация (фильтры по типу контента)

Когда нужно по-разному реагировать на текст/стикеры/анимации.

```python
from maxpybot.dispatcher import F
from maxpybot.dispatcher.router import Router
from maxpybot.types import Message

router = Router()

@router.message(F.text)
async def on_text(message: Message) -> None:
    print("Text:", message.body.text)

@router.message(F.sticker)
async def on_sticker(message: Message) -> None:
    print("Sticker in chat:", message.chat.chat_id)

@router.message(F.video)
async def on_video(message: Message) -> None:
    print("Video (в т.ч. GIF в MAX) in chat:", message.chat.chat_id)
```

## 3) Уведомления по deep links

Когда нужно разделять обычные старты и реферальные диплинки.

```python
from maxpybot.dispatcher.filters import start_payload_is
from maxpybot.dispatcher.router import Router
from maxpybot.types import BotStartedUpdate

router = Router()

@router.bot_started(start_payload_is("promo_summer2025"))
async def on_promo_start(update: BotStartedUpdate) -> None:
    print("Campaign hit:", update.start_payload)
```

## 4) Модульная структура роутеров

Когда хендлеры разложены по файлам (`handlers/questions.py`, `handlers/media.py`).

```python
from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher
from handlers import media, questions

bot = MaxBot("TOKEN")
dp = Dispatcher()
dp.include_routers(questions.router, media.router)
```
