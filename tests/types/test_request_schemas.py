import pytest

from maxpybot.types import (
    BotPatchSchema,
    ChatPatchSchema,
    SubscriptionSchema,
    build_request_payload,
)


def test_build_request_payload_accepts_schema_model() -> None:
    payload = build_request_payload(BotPatchSchema(first_name="Max"), BotPatchSchema)
    assert payload == {"first_name": "Max"}


def test_build_request_payload_accepts_raw_dict() -> None:
    payload = build_request_payload({"title": "New title"}, ChatPatchSchema)
    assert payload == {"title": "New title"}


def test_subscription_schema_supports_deprecated_subscribe_url_alias() -> None:
    with pytest.warns(DeprecationWarning):
        payload = build_request_payload(
            {"subscribe_url": "https://bot.example.com/webhook", "secret": "s3cr3t"},
            SubscriptionSchema,
        )
    assert payload["url"] == "https://bot.example.com/webhook"
    assert payload["secret"] == "s3cr3t"
