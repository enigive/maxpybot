# Webhook и subscriptions

Webhook-подписки можно управлять напрямую через `bot`.

## Привязать webhook

```python
await bot.subscribe_webhook(
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

`secret` из `subscribe_webhook(...)` должен совпадать с secret, который проверяет ваш
`WebhookHandler` по заголовку `X-Max-Bot-Api-Secret`.

Для ограничения источников webhook-запросов можно передать `allowed_ip_networks`
в `WebhookHandler` (поддерживаются CIDR-подсети и одиночные IP).

Для production-потока доступны:

- `max_processing_retries` — число повторных попыток обработки webhook при внутренней ошибке;
- `metrics` (`WebhookMetrics`) — счетчики обработки (`requests_total`, `processed_total`,
  `retried_total`, `failed_total` и т.д.).

## Отвязать конкретный webhook

```python
await bot.unsubscribe_webhook("https://bot.example.com/webhook")
```

## Отвязать все webhook

```python
await bot.unsubscribe_all_webhooks()
```

## Пример HTTPS webhook сервера

```python
from maxpybot import MaxBot
from maxpybot.dispatcher.router import Router
from maxpybot.dispatcher.webhook import WebhookMetrics
from maxpybot.types import Message

bot = MaxBot("YOUR_BOT_TOKEN")
WEBHOOK_SECRET = "CHANGE_ME"
ALLOWED_IP_NETWORKS = ["203.0.113.0/24", "2001:db8::/32"]
WEBHOOK_METRICS = WebhookMetrics()

router = Router()

@router.message_created()
async def on_message(message: Message) -> None:
    print(message.chat.chat_id, message.body.text)

bot.start_webhook(
    router=router,
    path="/webhook",
    host="127.0.0.1",
    port=8443,
    cert_path="cert.pem",
    key_path="key.pem",
    secret=WEBHOOK_SECRET,
    allowed_ip_networks=ALLOWED_IP_NETWORKS,
    max_processing_retries=2,
    metrics=WEBHOOK_METRICS,
    subscribe_url="https://bot.example.com/webhook",
    update_types=["message_created", "message_callback", "bot_started"],
    unsubscribe_on_shutdown=True,
)
```
