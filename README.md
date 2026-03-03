# maxpybot

Async Python framework for MAX bots with API parity-first approach.

## Goals

- Match current MAX Bot API operations/types/request bodies from upstream OpenAPI.
- Keep user-facing types stable with compatibility normalization for payload drift.
- Provide minimal dispatcher/router/filters, long polling, and webhook handling.

## Source of truth

- Upstream Go SDK and schema: <https://github.com/max-messenger/max-bot-api-client-go>
- Synced OpenAPI file in this repo: `vendor/max_bot_api/schema.yaml`

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
```

## Docs and examples

- Documentation index: `docs/README.md`
- Cookbook: `docs/cookbook.md`
- Migration guide: `MIGRATION.md`
- Release checklist: `docs/release-checklist.md`
- Changelog: `CHANGELOG.md`
- Examples directory: `examples/`
- Next milestones: `ROADMAP.md`

## Public types

```python
from maxpybot.types import User, Chat, Message
```

Request schemas are also available from `maxpybot.types` (for example, `NewMessageSchema`).

## FSM and storage

```python
from maxpybot.fsm import FSMContext, MemoryStorage
```

Available adapters:

- `MemoryStorage` (built-in)
- `RedisStorage` (optional, requires `redis` package)

## Quick start (polling)

```python
import asyncio

from maxpybot import MaxBot
from maxpybot.dispatcher import Dispatcher, F
from maxpybot.dispatcher.router import Router
from maxpybot.types import Message


async def main() -> None:
    bot = MaxBot("YOUR_BOT_TOKEN")
    dp = Dispatcher()
    router = Router()

    @router.message(F.text)
    async def on_text(message: Message) -> None:
        await message.answer(text="Hello from maxpybot")

    dp.include_router(router)
    await dp.start_polling(bot)


asyncio.run(main())
```

## Quick start (webhook, aiohttp)

```python
from maxpybot import MaxBot
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookMetrics
from maxpybot.types import Message

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://bot.example.com/webhook"
WEBHOOK_SECRET = "CHANGE_ME"
ALLOWED_IP_NETWORKS = ["203.0.113.0/24"]
WEBHOOK_METRICS = WebhookMetrics()


def run_webhook_server() -> None:
    bot = MaxBot("YOUR_BOT_TOKEN")
    router = Router()
    
    @router.message_created()
    async def on_message(message: Message) -> None:
        await message.answer(text="Webhook is active")

    bot.start_webhook(
        router=router,
        path=WEBHOOK_PATH,
        host="127.0.0.1",
        port=8443,
        cert_path="cert.pem",
        key_path="key.pem",
        secret=WEBHOOK_SECRET,
        allowed_ip_networks=ALLOWED_IP_NETWORKS,
        max_processing_retries=2,
        metrics=WEBHOOK_METRICS,
        subscribe_url=WEBHOOK_URL,
        unsubscribe_on_shutdown=True,
    )
```

## Deep links and start payload

```python
from maxpybot.dispatcher import F
from maxpybot.dispatcher.router import Router
from maxpybot.types import BotStartedUpdate, Message

router = Router()


@router.bot_started(F.start_payload == "promo_summer2025")
async def on_started(update: BotStartedUpdate) -> None:
    print(update.start_payload)  # -> "promo_summer2025"


@router.message_created(F.start_payload == "ref_user456789")
async def on_start_message(message: Message) -> None:
    print(message.start_payload)  # -> "ref_user456789" for "/start ref_user456789"
```

## OpenAPI sync and model generation

```bash
python tools/sync_max_openapi.py
python tools/generate_models.py
```

Generated artifacts:

- `maxpybot/types/generated/models.py`
- `maxpybot/types/generated/openapi_meta.py`

## Test

```bash
.venv/bin/pytest
```
