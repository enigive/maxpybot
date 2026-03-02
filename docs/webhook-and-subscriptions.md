# Webhook и subscriptions

Webhook-подписки управляются через `api.subscriptions`.

## Привязать webhook

```python
await api.subscriptions.subscribe(
    subscribe_url="https://bot.example.com/webhook",
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
```

## Отвязать конкретный webhook

```python
await api.subscriptions.unsubscribe("https://bot.example.com/webhook")
```

## Отвязать все webhook

```python
await api.subscriptions.unsubscribe_all()
```

## Пример HTTPS webhook сервера

```python
import ssl
from aiohttp import web

from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookHandler

router = Router()
handler = WebhookHandler(router)

app = web.Application()
app.router.add_post("/webhook", handler.handle)

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain("cert.pem", "key.pem")

web.run_app(app, host="127.0.0.1", port=8443, ssl_context=ssl_context)
```
