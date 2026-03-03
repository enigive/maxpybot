# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows SemVer.

## [Unreleased]

### Added

- `Dispatcher` facade with `include_router(s)`, `start_polling`, and `start_webhook`.
- `F` filter namespace (`F.text`, `F.sticker`, `F.video`, `F.image`, …) для удобной записи фильтров.
- Deep-link/start filters (`has_start_payload`, `start_payload_is`, `start_payload_matches`).
- FSM module (`MemoryStorage`, optional `RedisStorage`, `FSMContext`).
- CI workflows (tests, lint, type checks, coverage, smoke examples).

### Changed

- Public entrypoint renamed to `MaxBot` (legacy `MaxBotAPI` removed).
- Typed-first dispatcher/handler API with signature-based injection.
- Public DTO layer expanded to remove `Any` from known fields where possible.

### Docs

- Expanded endpoint group docs with request/response examples.
- Added cookbook, migration guide, and release checklist.
