# Release checklist

Короткий чеклист перед публикацией новой версии.

## Подготовка версии

- Обновить `CHANGELOG.md` (новая секция версии, дата, ключевые изменения).
- Проверить `MIGRATION.md`, если есть breaking changes.
- Проверить `ROADMAP.md` и отметить выполненные пункты.
- Проверить версию в `pyproject.toml`.

## Качество

- Запустить тесты: `.venv/bin/pytest`.
- Запустить линт: `.venv/bin/ruff check .`.
- Запустить type checks: `.venv/bin/mypy maxpybot`.
- Проверить coverage: `.venv/bin/pytest --cov=maxpybot --cov-report=term --cov-report=xml`.

## Артефакты

- Собрать wheel/sdist: `.venv/bin/python -m build`.
- Проверить пакеты: `.venv/bin/twine check dist/*`.
- Подписать артефакты через release workflow (Sigstore/OIDC).

## Публикация

- Запустить workflow публикации вручную.
- Проверить, что release-артефакты и подписи опубликованы.
- Создать git tag релиза.

## После публикации

- Проверить установку пакета в чистом окружении.
- Прогнать smoke-примеры.
- Обновить статус релиза в changelog/roadmap.
