from maxpybot.api.bots import BotsAPI
from maxpybot.api.chats import ChatsAPI
from maxpybot.api.messages import MessagesAPI
from maxpybot.api.subscriptions import SubscriptionsAPI
from maxpybot.api.uploads import UploadsAPI
from maxpybot.api_client import MaxBot
from maxpybot.types.generated.openapi_meta import OPERATION_DEFINITIONS, OPERATION_IDS


def test_operation_id_coverage() -> None:
    classes = [BotsAPI, ChatsAPI, MessagesAPI, SubscriptionsAPI, UploadsAPI]

    missing = []
    for operation_id in OPERATION_IDS:
        if operation_id == "getUpdates":
            if not hasattr(MaxBot, operation_id):
                missing.append(operation_id)
            continue
        if not any(hasattr(cls, operation_id) for cls in classes):
            missing.append(operation_id)

    assert missing == []


def test_operation_definition_count() -> None:
    assert len(OPERATION_IDS) == len(OPERATION_DEFINITIONS)
    assert len(OPERATION_IDS) == 31


def test_subscriptions_has_unsubscribe_all_helper() -> None:
    assert hasattr(SubscriptionsAPI, "unsubscribe_all")
