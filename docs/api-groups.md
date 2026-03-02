# API группы и методы

Текущие группы находятся в `maxpybot/api/`.

## BotsAPI

- `get_my_info()` / `getMyInfo`
- `edit_my_info(patch)` / `editMyInfo`

## ChatsAPI

- `get_chats(count=None, marker=None)` / `getChats`
- `get_chat_by_link(chat_link)` / `getChatByLink`
- `get_chat(chat_id)` / `getChat`
- `edit_chat(chat_id, patch)` / `editChat`
- `delete_chat(chat_id)` / `deleteChat`
- `send_action(chat_id, action)` / `sendAction`
- `get_pinned_message(chat_id)` / `getPinnedMessage`
- `pin_message(chat_id, body)` / `pinMessage`
- `unpin_message(chat_id)` / `unpinMessage`
- `get_membership(chat_id)` / `getMembership`
- `leave_chat(chat_id)` / `leaveChat`
- `get_admins(chat_id)` / `getAdmins`
- `post_admins(chat_id, admins)` / `postAdmins`
- `delete_admins(chat_id, user_id)` / `deleteAdmins`
- `get_members(chat_id, user_ids=None, marker=None, count=None)` / `getMembers`
- `add_members(chat_id, users_body)` / `addMembers`
- `remove_member(chat_id, user_id)` / `removeMember`

## MessagesAPI

- `get_messages(chat_id=None, message_ids=None, from_marker=None, to_marker=None, count=None)` / `getMessages`
- `send_message(body, chat_id=None, user_id=None)` / `sendMessage`
- `edit_message(message_id, body)` / `editMessage`
- `delete_message(message_id)` / `deleteMessage`
- `get_message_by_id(message_id)` / `getMessageById`
- `get_video_attachment_details(video_token)` / `getVideoAttachmentDetails`
- `answer_on_callback(callback_id, callback)` / `answerOnCallback`

## SubscriptionsAPI

- `get_subscriptions()` / `getSubscriptions`
- `subscribe(subscribe_url, update_types=None, secret="")`
- `unsubscribe(subscription_url)`
- `unsubscribe_all()` / `unsubscribeAll`

## UploadsAPI

- `get_upload_url(upload_type)` / `getUploadUrl`
- `upload_media_from_reader(upload_type, reader, file_name=None)`
- `upload_media_from_file(upload_type, file_path)`
- `upload_media_from_url(upload_type, url)`

## MaxBotAPI

- Группы:
  - `api.bots`
  - `api.chats`
  - `api.messages`
  - `api.subscriptions`
  - `api.uploads`
- Апдейты:
  - `get_updates(...)` / `getUpdates`
  - `iter_updates(...)` / `iterUpdates`
