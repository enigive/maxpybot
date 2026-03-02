# Апдейты и dispatcher

## Поддерживаемые типы апдейтов

Текущий список типов, которые учитываются в compat-слое:

- `message_created`
- `message_callback`
- `message_edited`
- `message_removed`
- `bot_added`
- `bot_removed`
- `dialog_muted`
- `dialog_unmuted`
- `dialog_cleared`
- `dialog_removed`
- `user_added`
- `user_removed`
- `bot_started`
- `bot_stopped`
- `chat_title_changed`
- `message_chat_created`

`UpdateParser`:

- нормализует payload и сохраняет `raw_payload`;
- разбирает вложения сообщений через `type`;
- для незнакомых/неполных схем возвращает безопасный fallback.

## Router

`Router` поддерживает:

- регистрацию через `register(...)`;
- декораторы `on_update(...)`, `message(...)`, `callback_query(...)`;
- вложенные роутеры (`include_router`);
- middleware hooks `middleware_before(...)`, `middleware_after(...)`, `middleware_error(...)`;
- централизованные `error handlers` через `on_error(...)` (включая цепочку parent/child router);
- фильтры (sync/async);
- `dispatch(update)`.

## Filters

Базовые фильтры в `maxpybot/dispatcher/filters.py`:

- `update_type_is(expected)`
- `chat_id_is(expected_chat_id)`
- `text_contains(needle)`
- `text_matches(pattern, flags=0)` (regex)
- `chat_type_is(expected_chat_type)`
- `sender_id_is(expected_sender_id)`
- `callback_payload_is(expected_payload)`

## PollingRunner

`PollingRunner(api, router).run(...)`:

- поддерживает lifecycle hooks: `on_start(...)`, `on_stop(...)`, `on_shutdown(...)`;
- позволяет останавливать polling через `stop()`;
- читает поток апдейтов через `api.iter_updates(...)`;
- прокидывает каждый апдейт в `router.dispatch(...)`.

## WebhookHandler

`WebhookHandler(router).handle(request)`:

- принимает только `POST`;
- валидирует JSON body;
- парсит апдейт через `UpdateParser`;
- отправляет апдейт в роутер.
