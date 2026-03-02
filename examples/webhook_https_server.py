import ssl
from typing import List

from aiohttp import web

from maxpybot import MaxBotAPI
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookHandler

BOT_TOKEN = "YOUR_BOT_TOKEN"
WEBHOOK_URL = "https://bot.example.com/webhook"
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "CHANGE_ME"

UPDATE_TYPES: List[str] = [
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
]


def main() -> None:
    api = MaxBotAPI(BOT_TOKEN)
    router = Router()
    handler = WebhookHandler(router)

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handler.handle)

    async def on_startup(_: web.Application) -> None:
        await api.subscriptions.subscribe(
            subscribe_url=WEBHOOK_URL,
            update_types=UPDATE_TYPES,
            secret=WEBHOOK_SECRET,
        )

    async def on_cleanup(_: web.Application) -> None:
        await api.subscriptions.unsubscribe(WEBHOOK_URL)
        await api.close()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("cert.pem", "key.pem")

    web.run_app(app, host="127.0.0.1", port=8443, ssl_context=ssl_context)


if __name__ == "__main__":
    main()
