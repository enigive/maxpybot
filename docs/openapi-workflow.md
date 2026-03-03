# OpenAPI workflow (внутренний для разработки)

Этот процесс нужен maintainers для синхронизации с upstream MAX OpenAPI.
Для пользователей это не публичный контракт библиотеки.

## Источник

- Upstream Go SDK: `max-messenger/max-bot-api-client-go`
- Файл схемы: `schemes/schema.yaml`

## Dev-процесс

1. Синхронизировать upstream-схему:

```bash
python tools/sync_max_openapi.py
```

2. Обновить generated-модели и метаданные операций:

```bash
python tools/generate_models.py
```

## Артефакты (implementation details)

- `vendor/max_bot_api/schema.yaml` — локальная копия upstream OpenAPI
- `maxpybot/types/generated/models.py` — generated pydantic-модели
- `maxpybot/types/generated/openapi_meta.py` — `operationId` + mapping method/path

## Контроль parity

- Тест: `tests/api/test_operation_parity.py`
- Цель: не допускать пропусков `operationId` и случайных endpoint/body вне OpenAPI

## Что является публичным контрактом для пользователей

- Публичные request-схемы: `maxpybot/types/schemas.py`
- API-методы принимают как схемы, так и `dict` для обратной совместимости
- Слой адаптеров: `maxpybot/types/adapters.py` (валидация и нормализация перед transport)

## Политика совместимости

- Изменения upstream OpenAPI сначала попадают в dev workflow и generated-слой.
- Пользовательские схемы обновляются отдельно и предсказуемо, с alias/deprecation-политикой.
