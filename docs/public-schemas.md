# Публичные схемы и DTO

Пользовательский контракт для входных `body/patch` живет в `maxpybot/types/schemas.py`.

Generated-модели из OpenAPI остаются внутренней реализацией и не являются обязательной
точкой интеграции для кода пользователей.

## Публичные DTO для ответов и апдейтов

Ключевые типы теперь доступны напрямую из `maxpybot.types`:

- `User`
- `Chat`
- `Message`
- и связанные DTO (`BotInfo`, `MessageList`, `SendMessageResult`, `Subscription`, ...)

Пример импорта:

```python
from maxpybot.types import User, Chat, Message
```

Эти DTO подключены в runtime-валидацию, поэтому API по возможности возвращает именно
публичные классы, а не generated-классы напрямую.

## Где используются схемы

- `BotPatchSchema` → `bot.bots.edit_my_info(...)`
- `ChatPatchSchema` → `bot.chats.edit_chat(...)`
- `SendActionSchema` → `bot.chats.send_action(...)`
- `PinMessageSchema` → `bot.chats.pin_message(...)`
- `ChatAdminsSchema` → `bot.chats.post_admins(...)`
- `UserIdsSchema` → `bot.chats.add_members(...)`
- `NewMessageSchema` → `bot.messages.send_message(...)`, `bot.messages.edit_message(...)`
- `CallbackAnswerSchema` → `bot.messages.answer_on_callback(...)`
- `SubscriptionSchema` → внутренне используется в `bot.subscriptions.subscribe(...)`

Для отправки сообщений **без JSON** (и без сборки `NewMessageSchema` вручную) используйте high-level методы:
`bot.send_message/send_image/send_video/...` — см. `docs/sending-messages.md`.

## Пример

Ниже показан низкоуровневый вариант (полезно, когда вы хотите формировать payload строго схемами).

```python
from maxpybot.types import NewMessageSchema
from maxpybot.types.generated.models import AttachmentRequest

body = NewMessageSchema(
    text="hello",
    link={},
    attachments=[AttachmentRequest(type="image")],
)

await bot.messages.send_message(body=body, chat_id=123)
```

## NewMessageSchema: вложения и клавиатуры

Для практических примеров (фото/видео/файлы, inline/reply клавиатуры, share/location) см.:

- `docs/sending-messages.md`

Напоминание: при использовании низкоуровневого `dict`/`NewMessageSchema` для отправки **должны присутствовать**
как минимум ключи `text`, `attachments`, `link` (их можно передавать пустыми: `attachments=[]`, `link={}`).

## Обратная совместимость

- Методы продолжают принимать `dict` (legacy usage).
- Перед отправкой payload проходит через единый адаптер `build_request_payload(...)`.
- В публичных схемах можно безопасно добавлять alias и `DeprecationWarning` без изменения transport-слоя.
- Generated-слой остается внутренним механизмом синхронизации с OpenAPI.
