# API группы и методы

Бизнес-методы API доступны через объект `bot`:

- `bot.bots`
- `bot.chats`
- `bot.messages`
- `bot.subscriptions`
- `bot.uploads`

Ниже перечислены все группы и минимальные примеры запроса/ответа.

## BotsAPI

- `get_my_info()` / `getMyInfo`
- `edit_my_info(patch: BotPatchSchema | dict)` / `editMyInfo`

Пример:

```python
me = await bot.bots.get_my_info()
print(me.user_id, me.username)

updated = await bot.bots.edit_my_info({"description": "Support bot"})
print(updated.success)
```

Типичный ответ `get_my_info()`:

```json
{
  "user_id": "123456",
  "username": "support_bot",
  "first_name": "Support",
  "last_name": "Bot",
  "is_bot": true
}
```

## ChatsAPI

- `get_chats(count=None, marker=None)` / `getChats`
- `get_chat_by_link(chat_link)` / `getChatByLink`
- `get_chat(chat_id)` / `getChat`
- `edit_chat(chat_id, patch: ChatPatchSchema | dict)` / `editChat`
- `delete_chat(chat_id)` / `deleteChat`
- `send_action(chat_id, action: str | SendActionSchema)` / `sendAction`
- `get_pinned_message(chat_id)` / `getPinnedMessage`
- `pin_message(chat_id, body: PinMessageSchema | dict)` / `pinMessage`
- `unpin_message(chat_id)` / `unpinMessage`
- `get_membership(chat_id)` / `getMembership`
- `leave_chat(chat_id)` / `leaveChat`
- `get_admins(chat_id)` / `getAdmins`
- `post_admins(chat_id, admins: ChatAdminsSchema | dict)` / `postAdmins`
- `delete_admins(chat_id, user_id)` / `deleteAdmins`
- `get_members(chat_id, user_ids=None, marker=None, count=None)` / `getMembers`
- `add_members(chat_id, users_body: UserIdsSchema | dict)` / `addMembers`
- `remove_member(chat_id, user_id)` / `removeMember`

Пример:

```python
chat = await bot.chats.get_chat(chat_id=1234567890)
print(chat.chat_id, chat.title)

await bot.chats.send_action(chat_id=chat.chat_id, action="typing_on")
```

Типичный ответ `get_chat(...)`:

```json
{
  "chat_id": 1234567890,
  "title": "Support",
  "description": "Support channel",
  "type": "chat",
  "status": "active"
}
```

## MessagesAPI

- `get_messages(chat_id=None, message_ids=None, from_marker=None, to_marker=None, count=None)` / `getMessages`
- `send_message(body: NewMessageSchema | dict, chat_id=None, user_id=None)` / `sendMessage`
- `edit_message(message_id, body: NewMessageSchema | dict)` / `editMessage`
- `delete_message(message_id)` / `deleteMessage`
- `get_message_by_id(message_id)` / `getMessageById`
- `get_video_attachment_details(video_token)` / `getVideoAttachmentDetails`
- `answer_on_callback(callback_id, callback: CallbackAnswerSchema | dict)` / `answerOnCallback`

Про вложения (фото/видео/файлы), клавиатуры и форматирование текста: `docs/sending-messages.md`.

Пример:

```python
sent = await bot.send_message(chat_id=1234567890, text="Hello from maxpybot")
print(sent.message.body.text)
```

Типичный ответ `send_message(...)`:

```json
{
  "message": {
    "timestamp": 1710000000,
    "recipient": {"chat_id": 1234567890, "chat_type": "chat", "user_id": 0},
    "body": {"mid": "m-1", "seq": 1, "text": "Hello from maxpybot", "attachments": []}
  }
}
```

## SubscriptionsAPI

- `get_subscriptions()` / `getSubscriptions`
- `subscribe(subscribe_url, update_types=None, secret="")`
- `unsubscribe(subscription_url)`
- `unsubscribe_all()` / `unsubscribeAll`

Пример:

```python
result = await bot.subscribe_webhook(
    subscribe_url="https://bot.example.com/webhook",
    update_types=["message_created", "message_callback", "bot_started"],
    secret="CHANGE_ME",
)
print(result.success)
```

Типичный ответ `get_subscriptions()`:

```json
{
  "subscriptions": [
    {
      "url": "https://bot.example.com/webhook",
      "update_types": ["message_created", "message_callback", "bot_started"]
    }
  ]
}
```

## UploadsAPI

- `get_upload_url(upload_type)` / `getUploadUrl`
- `upload_media_from_reader(upload_type, reader, file_name=None)`
- `upload_media_from_file(upload_type, file_path)`
- `upload_media_from_url(upload_type, url)`

Пример:

```python
endpoint = await bot.uploads.get_upload_url("image")
print(endpoint.url)

uploaded = await bot.uploads.upload_media_from_url("image", "https://example.com/image.jpg")
print(uploaded.token)
```

Типичный ответ `get_upload_url(...)`:

```json
{
  "url": "https://upload.max.ru/bot-api/upload/...",
  "token": "upload-token"
}
```

## MaxBot helpers

Кроме прямых API-групп, `MaxBot` дает high-level helpers:

- отправка сообщений без `body`/dict:
  - `send_message(...)`
  - `send_image(...)`
  - `send_video(...)`
  - `send_audio(...)`
  - `send_file(...)`
  - `send_sticker(...)`
  - `send_contact(...)`
  - `send_location(...)`
  - `send_share(...)`
- `start_polling(router, marker=None, types=None)`
- `create_webhook_app(...)`
- `start_webhook(...)`
- `subscribe_webhook(...)`
- `unsubscribe_webhook(...)`
- `unsubscribe_all_webhooks()`
- `get_updates(...)` / `getUpdates`
- `iter_updates(...)` / `iterUpdates`
