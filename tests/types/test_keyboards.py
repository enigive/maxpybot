from maxpybot.types import (
    InlineCallbackButton,
    InlineChatButton,
    InlineKeyboard,
    InlineOpenAppButton,
    ReplyContactButton,
    ReplyGeoLocationButton,
    ReplyKeyboard,
    ReplyMessageButton,
)


def test_inline_keyboard_to_attachment_request() -> None:
    kb = InlineKeyboard.from_rows(
        InlineKeyboard.row(InlineCallbackButton(text="OK", payload="ok")),
        InlineKeyboard.row(InlineChatButton(text="Discuss", chat_title="T")),
        InlineKeyboard.row(InlineOpenAppButton(text="Open App", web_app="myapp", payload="p")),
    )
    assert kb.to_attachment_request() == {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "OK", "payload": "ok"}],
                [{"type": "chat", "text": "Discuss", "chat_title": "T"}],
                [{"type": "open_app", "text": "Open App", "web_app": "myapp", "payload": "p"}],
            ]
        },
    }


def test_reply_keyboard_to_attachment_request() -> None:
    kb = ReplyKeyboard.from_rows(
        ReplyKeyboard.row(
            ReplyMessageButton(text="Yes", payload="yes"),
            ReplyMessageButton(text="No", payload="no"),
        ),
        ReplyKeyboard.row(
            ReplyGeoLocationButton(text="Geo"),
            ReplyContactButton(text="Contact"),
        ),
    )
    assert kb.to_attachment_request() == {
        "type": "reply_keyboard",
        "buttons": [
            [
                {"type": "message", "text": "Yes", "payload": "yes"},
                {"type": "message", "text": "No", "payload": "no"},
            ],
            [
                {"type": "user_geo_location", "text": "Geo"},
                {"type": "user_contact", "text": "Contact"},
            ],
        ],
    }

