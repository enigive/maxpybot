# Публичные типы и схемы (`maxpybot.types`)

`maxpybot.types` — это **публичный контракт** библиотеки: DTO для ответов/апдейтов и pydantic-схемы для request payloads.

Импорт:

```python
from maxpybot.types import Message, Chat, User
from maxpybot.types import NewMessageSchema
```

## 0) База и утилиты

- `MaxBaseModel` — базовый pydantic-модельный класс (forward-compatible: `extra="allow"`)
- `AttachmentType` — enum типов вложений (используется в filters и при разборе `MessageBody.attachments`)
- `build_request_payload(payload, schema)` — нормализует `dict`/pydantic-модель в валидный request payload (используется внутри API групп)

## 0.1) Клавиатуры (типизированные)

Для отправки сообщений **без JSON** используются типы клавиатур:

- `InlineKeyboard` и кнопки: `InlineCallbackButton`, `InlineLinkButton`, `InlineRequestContactButton`,
  `InlineRequestGeoLocationButton`, `InlineChatButton`, `InlineMessageButton`
- `ReplyKeyboard` и кнопки: `ReplyMessageButton`, `ReplyGeoLocationButton`, `ReplyContactButton`

Практика: `docs/sending-messages.md`.

## 1) Request-схемы (body/patch)

Эти схемы предназначены для формирования `body/patch` в API-методах. Все методы также продолжают принимать обычный `dict`.

- `BotPatchSchema`
  - **Где используется**: `bot.bots.edit_my_info(...)`
  - **Поля**: `first_name`, `name`, `description`, `commands`, `photo`, ...

- `ChatPatchSchema`
  - **Где используется**: `bot.chats.edit_chat(...)`
  - **Поля**: `title`, `icon`, `notify`, `pin`, ...

- `SendActionSchema`
  - **Где используется**: `bot.chats.send_action(...)`
  - **Поля**: `action` (например: `typing_on`, `sending_photo`, ...)

- `PinMessageSchema`
  - **Где используется**: `bot.chats.pin_message(...)`
  - **Поля**: `message_id`, `notify`

- `ChatAdminsSchema`
  - **Где используется**: `bot.chats.post_admins(...)`

- `UserIdsSchema`
  - **Где используется**: `bot.chats.add_members(...)`

- `NewMessageSchema`
  - **Где используется**: `bot.messages.send_message(...)`, `bot.messages.edit_message(...)`
  - **Поля**: `text`, `attachments`, `link`, `notify`, `format`
  - **Практика**: отправка фото/клавиатур и др. — см. `docs/sending-messages.md`

- `CallbackAnswerSchema`
  - **Где используется**: `bot.messages.answer_on_callback(...)`
  - **Поля**: `notification`, `message`

- `SubscriptionSchema`
  - **Где используется**: внутренне в `bot.subscriptions.subscribe(...)`
  - **Поля**: `url`, `update_types`, `secret`, `version`

Подробнее про request-схемы и совместимость: `docs/public-schemas.md`.

## 2) DTO ответов (ключевые)

Ниже — наиболее часто используемые DTO:

- `User` — информация о пользователе/боте
- `Chat` — чат/канал
- `ChatIcon` — иконка/аватар чата (если доступно)
- `Message` — сообщение
- `MessageBody` — содержимое сообщения (`text`, `attachments`, `markup`, ...)
- `Recipient` — получатель сообщения (в `Message.recipient`), есть удобный alias `Message.chat`
- `MessageSender` — отправитель сообщения (может отсутствовать, если сообщение «от канала»)
- `MessageStat` — статистика (например, просмотры)
- `MessageLink` — linked message (reply/forward) в ответах API
- `Callback` — callback-событие от inline-кнопки

Почти все DTO построены поверх generated-моделей и имеют forward-compatible поведение:

- новые поля от MAX не должны ломать парсинг (pydantic `extra="allow"`)
- исходный payload может сохраняться в `raw_payload` (где применимо)

### Полный список публичных DTO/результатов

Все объекты, которые экспортирует `maxpybot.types` (кроме request-схем), сгруппированы ниже:

- **Bots/Chats**
  - `User`
  - `Chat`
  - `ChatIcon`
  - `BotInfo`
  - `ChatList`
  - `ChatMember`
  - `ChatMembersList`
  - `GetPinnedMessageResult`

- **Messages**
  - `Message`
  - `MessageBody`
  - `MessageSender`
  - `MessageStat`
  - `MessageLink`
  - `Recipient`
  - `MessageList`
  - `SendMessageResult`
  - `SimpleQueryResult`
  - `Callback`
  - `VideoAttachmentDetails`

- **Subscriptions**
  - `GetSubscriptionsResult`
  - `Subscription`

- **Uploads**
  - `UploadEndpoint`
  - `UploadedInfo`
  - `PhotoTokens`

## 3) Апдейты (updates)

`Update` — базовый тип апдейта, а также набор типизированных update DTO:

- `Update`
- `MessageCreatedUpdate`
- `MessageEditedUpdate`
- `MessageRemovedUpdate`
- `MessageCallbackUpdate`
- `BotAddedToChatUpdate`, `BotRemovedFromChatUpdate`
- `UserAddedToChatUpdate`, `UserRemovedFromChatUpdate`
- `BotStartedUpdate`, `BotStoppedUpdate`
- `ChatTitleChangedUpdate`
- `MessageChatCreatedUpdate`
- `DialogLifecycleUpdate` (база для dialog-* апдейтов)
- `DialogMutedUpdate`, `DialogUnmutedUpdate`, `DialogClearedUpdate`, `DialogRemovedUpdate`
- `UnknownUpdate` — fallback для неизвестных/битых payload

Подробнее про routing и обработку апдейтов: `docs/updates-and-dispatcher.md`.

## 4) Вложения (attachments) в входящих сообщениях

В `MessageBody.attachments` лежит список вложений. В compat-слое они по возможности приводятся
к типизированным моделям по `type`:

- `image` → `PhotoAttachment`
- `video` → `VideoAttachment`
- `audio` → `AudioAttachment`
- `file` → `FileAttachment`
- `contact` → `ContactAttachment`
- `sticker` → `StickerAttachment`
- `share` → `ShareAttachment`
- `location` → `LocationAttachment`
- `inline_keyboard` → `InlineKeyboardAttachment`

Если тип неизвестен, вложение может остаться «сырым» `dict`.

Для проверки типа удобно использовать enum `AttachmentType`:

```python
from maxpybot.types import AttachmentType, Message


def has_image(message: Message) -> bool:
    for att in message.body.attachments:
        if getattr(att, "type", None) == AttachmentType.IMAGE.value:
            return True
    return False
```

## 5) Generated модели (полная схема MAX OpenAPI)

Файл `maxpybot/types/generated/models.py` содержит auto-generated pydantic-модели по OpenAPI.
Они полезны, когда нужна строгая типизация для payload кнопок/вложений, но не являются
обязательной точкой интеграции.

Полный «source of truth» по структурам — `vendor/max_bot_api/schema.yaml`.

