# maxpybot

Async Python framework for MAX bots with API parity-first approach.

## Goals

- Match current MAX Bot API operations/types/request bodies from upstream OpenAPI.
- Keep user-facing types stable with compatibility normalization for payload drift.
- Provide minimal dispatcher/router/filters, long polling, and webhook handling.

## Source of truth

- Upstream Go client and schema: <https://github.com/max-messenger/max-bot-api-client-go>
- Synced OpenAPI file in this repo: `vendor/max_bot_api/schema.yaml`

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install ".[dev]"
```

## Docs and examples

- Documentation index: `docs/README.md`
- Examples directory: `examples/`
- Next milestones: `ROADMAP.md`

## Public types

```python
from maxpybot.types import User, Chat, Message
```

Request schemas are also available from `maxpybot.types` (for example, `NewMessageSchema`).

## Quick start (polling)

```python
import asyncio

from maxpybot import MaxBotAPI
from maxpybot.dispatcher.filters import text_contains
from maxpybot.dispatcher.polling import PollingRunner
from maxpybot.dispatcher.router import Router


async def main() -> None:
    api = MaxBotAPI("YOUR_BOT_TOKEN")
    router = Router()

    @router.message(text_contains("/start"))
    async def on_start(update):
        await api.messages.sendMessage(
            body={"text": "Hello from maxpybot"},
            chat_id=update.message.recipient.chat_id,
        )

    async with api:
        await PollingRunner(api, router).run()


asyncio.run(main())
```

## Quick start (webhook, aiohttp)

```python
import ssl

from aiohttp import web

from maxpybot import MaxBotAPI
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookHandler

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://bot.example.com/webhook"


async def setup_webhook(api: MaxBotAPI) -> None:
    await api.subscriptions.subscribe(
        subscribe_url=WEBHOOK_URL,
        update_types=[
            "message_created",
            "message_callback",
            "message_edited",
            "message_removed",
            "bot_added",
            "bot_removed",
            "dialog_muted",
            "dialog_unmuted",
            "dialog_cleared",
            "dialog_removed",
            "user_added",
            "user_removed",
            "bot_started",
            "bot_stopped",
            "chat_title_changed",
        ],
        secret="CHANGE_ME",
    )


async def remove_current_webhook(api: MaxBotAPI) -> None:
    await api.subscriptions.unsubscribe(WEBHOOK_URL)


async def remove_all_webhooks(api: MaxBotAPI) -> None:
    await api.subscriptions.unsubscribe_all()


def run_webhook_server() -> None:
    router = Router()
    handler = WebhookHandler(router)

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handler.handle)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    web.run_app(app, host="127.0.0.1", port=8443, ssl_context=ssl_context)
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
