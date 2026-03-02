# OpenAPI sync и генерация моделей

## Источник

- Upstream: `max-messenger/max-bot-api-client-go`
- Файл схемы: `schemes/schema.yaml`

## Локальный процесс

1. Синхронизировать схему:

```bash
python tools/sync_max_openapi.py
```

2. Сгенерировать модели и метаданные операций:

```bash
python tools/generate_models.py
```

## Результат генерации

- `vendor/max_bot_api/schema.yaml` — локальная копия upstream OpenAPI
- `maxpybot/types/generated/models.py` — generated pydantic-модели
- `maxpybot/types/generated/openapi_meta.py` — `operationId` + mapping method/path

## Проверка parity

- Контракт проверяется тестом `tests/api/test_operation_parity.py`
- Цель: не допускать «придуманных» endpoint/body и пропусков operationId
