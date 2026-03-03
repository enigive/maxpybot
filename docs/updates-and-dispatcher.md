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
- формализует `dialog_muted/dialog_unmuted/dialog_cleared/dialog_removed/bot_stopped`
  в публичные DTO (`Dialog*Update`, `BotStoppedUpdate`);
- для dialog-апдейтов поддерживает каноничный формат
  (`update_type`, `timestamp`, `chat_id`, `user`, `user_locale`);
- поддерживает deprecation-алиасы полей (`dialog_id`, `chatId`, `userId`, nested `dialog.*`)
  с `DeprecationWarning`;
- добавляет feature detection (`compat_capabilities`) и матрицу поддерживаемых
  возможностей (`compat_supported_capabilities`) для нестабильных update payloads;
- для незнакомых/неполных схем возвращает типизированный `UnknownUpdate`.

## Router

`Router` поддерживает:

- регистрацию через `register(...)`;
- broad-декоратор `on_update(...)` (advanced-сценарии);
- typed-декораторы:
  - `message_created(...)`, `message_callback(...)`, `message_edited(...)`, `message_removed(...)`
  - `bot_added(...)`, `bot_removed(...)`, `user_added(...)`, `user_removed(...)`
  - `bot_started(...)`, `bot_stopped(...)`, `chat_title_changed(...)`, `message_chat_created(...)`
  - `dialog_muted(...)`, `dialog_unmuted(...)`, `dialog_cleared(...)`, `dialog_removed(...)`
  - алиасы: `message(...)` -> `message_created(...)`, `callback_query(...)` -> `message_callback(...)`;
- вложенные роутеры (`include_router`);
- batch-подключение роутеров (`include_routers`);
- middleware hooks `middleware_before(...)`, `middleware_after(...)`, `middleware_error(...)`;
- централизованные `error handlers` через `on_error(...)` (включая цепочку parent/child router);
- инжекцию аргументов хендлера по сигнатуре (`message`, `callback`, `update`, `context`, `fsm`, `state`);
- фильтры (sync/async);
- `dispatch(update)`.

Рекомендуемый production-стиль: использовать конкретные typed-декораторы update-типов,
а не broad `on_update(...)`.

## Dispatcher

`Dispatcher` — это удобная обертка над корневым `Router`:

- `include_router(...)` и `include_routers(...)` для подключения модулей с хендлерами;
- `dispatch(update)` для ручного прокидывания апдейта;
- `start_polling(bot, ...)` и `start_webhook(bot, ...)` для запуска через `MaxBot`.

## Filters

Основной стиль — магические фильтры через `F`:

- контент: `F.text`, `F.sticker`, `F.image`, `F.video`, `F.audio`, `F.file`, `F.contact`,
  `F.inline_keyboard`, `F.share`, `F.location`;
- callback payload: `F.data`, `F.data == "back_home"`, `F.data.startswith("qst_")`;
- deep link/start: `F.start_payload`, `F.start_payload == "promo_summer2025"`,
  `F.start_payload.startswith("ref_")`;
- строки: `F.text.contains("hello")`, `F.text.lower().contains("привет")`,
  `F.text.startswith("/ban")`, `F.text.endswith("!")`, `F.text.regexp(r"(?i)^привет")`;
- композиция: `~F.text.startswith("spam")`, `(F.sender.id.in_({42, 777})) & F.text.contains("ban")`;
- коллекции/длина: `F.text.upper().in_({"PING", "PONG"})`, `F.text.len() > 5` (через сравнение результата `len()`).

`F.start_payload` работает как для `bot_started` (поле `payload`), так и для сообщений
со строкой вида `/start <payload>`.

Для attachment-типов используется `AttachmentType` enum:
`image`, `video`, `audio`, `file`, `sticker`, `contact`, `inline_keyboard`, `share`, `location`.

Функциональные фильтры (`text_contains(...)`, `start_payload_is(...)` и т.д.) остаются
доступны как совместимые обертки, но внутри они теперь основаны на `F`.

## PollingRunner

`PollingRunner(bot, router).run(...)`:

- поддерживает lifecycle hooks: `on_start(...)`, `on_stop(...)`, `on_shutdown(...)`;
- позволяет останавливать polling через `stop()`;
- читает поток апдейтов через `bot.iter_updates(...)`;
- прокидывает каждый апдейт в `router.dispatch(...)`.

Для простого старта можно использовать `MaxBot.start_polling(router, ...)`
без явного создания `PollingRunner`.

## WebhookHandler

`WebhookHandler(router).handle(request)`:

- принимает только `POST`;
- при заданном `secret` проверяет заголовок `X-Max-Bot-Api-Secret`;
- при заданном `allowed_ip_networks` ограничивает источники запросов по подсетям;
- валидирует JSON body;
- парсит апдейт через `UpdateParser`;
- поддерживает `max_processing_retries` для повторных попыток обработки;
- ведет `WebhookMetrics` и пишет предупреждения/ошибки в лог;
- отправляет апдейт в роутер.

Встроенные helper-фабрики:

- `create_webhook_app(...)` — собирает `aiohttp.web.Application` и регистрирует `POST` route.
- `create_https_ssl_context(cert_path, key_path)` — создает SSL context для запуска HTTPS webhook.
