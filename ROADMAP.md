# Roadmap

Файл фиксирует задачи после завершения Phase 1.  
Порядок можно уточнять по приоритету продукта.

## Статус выполнения

- Последнее выполненное: **2026-03-02** — Phase 8: настроены CI/release workflow,
  quality gates (lint/type/coverage), smoke-прогоны примеров и финализированы docs/DX-артефакты.
- История:
  - **2026-03-02** — Унифицирована терминология docs вокруг `bot`/`MaxBot`,
    добавлены cookbook, `MIGRATION.md`, `CHANGELOG.md`, `docs/release-checklist.md`
    и расширенные примеры request/response по endpoint-группам.
  - **2026-03-02** — Добавлен `Dispatcher` facade (`include_router(s)`,
    `start_polling/start_webhook`) и магические фильтры `F.text` / `F.sticker` / `F.video` и др.
  - **2026-03-02** — Добавлены CI workflows:
    matrix tests на Python 3.8+, lint (`ruff`), type checks (`mypy`),
    coverage gate + artifact report, release build/sign/publish prep.
  - **2026-03-02** — Добавлены smoke-тесты примеров (`tests/examples/test_examples_smoke.py`).
  - **2026-03-02** — Добавлен модуль `maxpybot.fsm`: `StorageKey`, `BaseStorage`,
    `FSMContext`, `create_fsm_context_from_update(...)`, `MemoryStorage`, `RedisStorage`.
  - **2026-03-02** — Добавлены тесты FSM/storage (`tests/fsm/*`) и пример
    `examples/fsm_feedback_flow.py` для многошагового stateful-сценария.
  - **2026-03-02** — Формализованы публичные DTO:
    `DialogMutedUpdate/DialogUnmutedUpdate/DialogClearedUpdate/DialogRemovedUpdate/BotStoppedUpdate`.
  - **2026-03-02** — Добавлены compat-нормализация старых/новых форматов payload,
    deprecation warnings на устаревшие поля и capability matrix + feature detection.
  - **2026-03-02** — В `WebhookHandler` добавлены `max_processing_retries`,
    `WebhookMetrics` и logging для rejected/failed webhook processing.
  - **2026-03-02** — Добавлены helper-фабрики webhook: `create_webhook_app(...)`
    (регистрация `POST` route + handler) и `create_https_ssl_context(...)`.
  - **2026-03-02** — В `WebhookHandler` добавлен allowlist по `allowed_ip_networks`
    (CIDR/одиночные IP), входящие запросы вне разрешённых подсетей отклоняются.
  - **2026-03-02** — В `WebhookHandler` добавлена проверка secret по заголовку
    `X-Max-Bot-Api-Secret` (matching с `secret` из `subscriptions.subscribe(...)`).
  - **2026-03-02** — В `dispatcher` добавлены middleware hooks (`before/after/error`),
    цепочка обработки ошибок для nested routers, фильтры `chat_type/sender/callback payload/regex`
    и lifecycle hooks в `PollingRunner` (`on_start/on_stop/on_shutdown` + `stop()`).
  - **2026-03-02** — Добавлены `maxpybot/types/models.py` и runtime-mapping на публичные DTO,
    API теперь возвращает публичные классы для известных моделей (`User/Chat/Message/...`).
  - **2026-03-02** — Добавлены `maxpybot/types/schemas.py`, `maxpybot/types/adapters.py`,
    тесты совместимости и обновлена документация по OpenAPI/public schemas.

## Phase 2: Укрепление API и типизации

- [x] Перевести входные `body/patch` из `Dict[str, Any]` в публичные typed-модели для всех API-групп. _(2026-03-02)_
- [x] Стабилизировать публичные DTO в `maxpybot/types` (обертки над generated-моделями). _(2026-03-02)_
- [x] Добавить единый слой адаптеров, чтобы отделить публичные модели от raw OpenAPI-структур. _(2026-03-02)_
- [x] Добавить тесты на обратную совместимость публичного API. _(2026-03-02)_

## Phase 3: Dispatcher и обработка событий

- [x] Добавить middleware pipeline (before/after/error hooks). _(2026-03-02)_
- [x] Добавить error handlers и централизованный перехват исключений хендлеров. _(2026-03-02)_
- [x] Добавить расширенные фильтры (по chat type, sender, callback payload, regex). _(2026-03-02)_
- [x] Добавить управление lifecycle polling (start/stop/shutdown hooks). _(2026-03-02)_

## Phase 4: Webhook production readiness

- [x] Добавить проверку webhook secret в `WebhookHandler`. _(2026-03-02)_
- [x] Добавить возможность ограничивать входящие IP по подсетям. _(2026-03-02)_
- [x] Добавить встроенные утилиты запуска HTTPS webhook (helper-фабрики для aiohttp app). _(2026-03-02)_
- [x] Добавить retry/metrics/logging для webhook processing. _(2026-03-02)_

## Phase 5: Compat и новые update payloads

- [x] Формализовать типы для `dialog_muted/dialog_unmuted/bot_stopped/dialog_cleared/dialog_removed`. _(2026-03-02)_
- [x] Добавить явные compat-тесты на старый и новый форматы payload. _(2026-03-02)_
- [x] Добавить deprecation-слой и предупреждения при изменении полей MAX API. _(2026-03-02)_
- [x] Ввести матрицу возможностей (capabilities) и feature detection для нестабильных зон API. _(2026-03-02)_

## Phase 6: Storage и stateful сценарии

- [x] Добавить FSM-модуль и интерфейсы хранилищ состояний. _(2026-03-02)_
- [x] Реализовать in-memory storage как базовый адаптер. _(2026-03-02)_
- [x] Добавить Redis storage как production-адаптер (опционально). _(2026-03-02)_
- [x] Добавить примеры многошаговых сценариев с состояниями. _(2026-03-02)_

## Phase 7: Документация и DX

- [x] Расширить docs по каждому endpoint-группе с примерами запросов/ответов. _(2026-03-02)_
- [x] Добавить cookbook для типовых кейсов (бот поддержки, модерация, уведомления). _(2026-03-02)_
- [x] Подготовить MIGRATION.md для будущих breaking changes. _(2026-03-02)_
- [x] Добавить changelog и release checklist. _(2026-03-02)_

## Phase 8: Инфраструктура и релизы

- [x] Настроить CI на Python 3.8+ (tests + lint + type checks). _(2026-03-02)_
- [x] Добавить quality gates и отчеты покрытия. _(2026-03-02)_
- [x] Подготовить публикацию пакета (версионирование, артефакты, подпись). _(2026-03-02)_
- [x] Добавить smoke-прогоны примеров в CI. _(2026-03-02)_
