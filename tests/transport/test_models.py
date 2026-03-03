import pytest
from maxpybot.transport.models import RequestOptions

def test_request_options_init() -> None:
    options = RequestOptions(
        method="GET",
        path="me",
        params={"v": "1.2.5"},
        authorized=True
    )
    assert options.method == "GET"
    assert options.path == "me"
    assert options.params == {"v": "1.2.5"}
    assert options.authorized is True

def test_request_options_defaults() -> None:
    options = RequestOptions(method="POST", path="messages")
    assert options.params is None
    assert options.authorized is True

def test_request_options_extra_forbid() -> None:
    with pytest.raises(ValueError):
        RequestOptions(method="GET", path="me", extra_field="forbidden")
