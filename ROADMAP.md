# Roadmap

Файл фиксирует задачи после завершения Phase 1.  
Порядок можно уточнять по приоритету продукта.

## Phase 2: Укрепление API и типизации

- Перевести входные `body/patch` из `Dict[str, Any]` в публичные typed-модели для всех API-групп.
- Стабилизировать публичные DTO в `maxpybot/types` (обертки над generated-моделями).
- Добавить единый слой адаптеров, чтобы отделить публичные модели от raw OpenAPI-структур.
- Добавить тесты на обратную совместимость публичного API.

## Phase 3: Dispatcher и обработка событий

- Добавить middleware pipeline (before/after/error hooks).
- Добавить error handlers и централизованный перехват исключений хендлеров.
- Добавить расширенные фильтры (по chat type, sender, callback payload, regex).
- Добавить управление lifecycle polling (start/stop/shutdown hooks).

## Phase 4: Webhook production readiness

- Добавить проверку webhook secret в `WebhookHandler`.
- Добавить возможность ограничивать входящие IP по подсетям.
- Добавить встроенные утилиты запуска HTTPS webhook (helper-фабрики для aiohttp app).
- Добавить retry/metrics/logging для webhook processing.

## Phase 5: Compat и новые update payloads

- Формализовать типы для `dialog_muted/dialog_unmuted/bot_stopped/dialog_cleared/dialog_removed`.
- Добавить явные compat-тесты на старый и новый форматы payload.
- Добавить deprecation-слой и предупреждения при изменении полей MAX API.
- Ввести матрицу возможностей (capabilities) и feature detection для нестабильных зон API.

## Phase 6: Storage и stateful сценарии

- Добавить FSM-модуль и интерфейсы хранилищ состояний.
- Реализовать in-memory storage как базовый адаптер.
- Добавить Redis storage как production-адаптер (опционально).
- Добавить примеры многошаговых сценариев с состояниями.

## Phase 7: Документация и DX

- Расширить docs по каждому endpoint-группе с примерами запросов/ответов.
- Добавить cookbook для типовых кейсов (бот поддержки, модерация, уведомления).
- Подготовить MIGRATION.md для будущих breaking changes.
- Добавить changelog и release checklist.

## Phase 8: Инфраструктура и релизы

- Настроить CI на Python 3.8+ (tests + lint + type checks).
- Добавить quality gates и отчеты покрытия.
- Подготовить публикацию пакета (версионирование, артефакты, подпись).
- Добавить smoke-прогоны примеров в CI.
