from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, get_args, get_origin

from typing_extensions import Annotated, get_type_hints

from ..fsm import FSMContext
from ..types import Callback, Message, Update
from ..types.base import MaxBaseModel
from .context import HandlerContext


class HandlerSignatureError(ValueError):
    pass


def validate_handler_signature(callback: Callable[..., Any]) -> None:
    signature = inspect.signature(callback)
    resolved_annotations = _resolve_callback_annotations(callback)
    parameters = list(signature.parameters.values())
    for parameter in parameters:
        if parameter.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            raise HandlerSignatureError(
                "Handler '{0}' uses unsupported parameter '{1}' ({2})".format(
                    callback.__name__,
                    parameter.name,
                    parameter.kind.name,
                )
            )
        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
            raise HandlerSignatureError(
                "Handler '{0}' uses positional-only parameter '{1}'".format(
                    callback.__name__,
                    parameter.name,
                )
            )

        supports = _supports_parameter(
            parameter,
            _resolved_parameter_annotation(parameter, resolved_annotations),
        )
        if not supports:
            raise HandlerSignatureError(
                "Handler '{0}' has unsupported parameter '{1}'".format(
                    callback.__name__,
                    parameter.name,
                )
            )


async def invoke_handler(callback: Callable[..., Any], context: HandlerContext) -> Any:
    signature = inspect.signature(callback)
    resolved_annotations = _resolve_callback_annotations(callback)
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    missing_required: List[str] = []

    for parameter in signature.parameters.values():
        resolved, has_value = _resolve_parameter_value(
            parameter,
            context,
            _resolved_parameter_annotation(parameter, resolved_annotations),
        )
        if not has_value:
            if parameter.default is not inspect.Parameter.empty:
                continue
            missing_required.append(parameter.name)
            continue

        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            args.append(resolved)
        else:
            kwargs[parameter.name] = resolved

    if missing_required:
        raise HandlerSignatureError(
            "Missing injectable values for handler '{0}': {1}".format(
                callback.__name__,
                ", ".join(missing_required),
            )
        )

    result = callback(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


def _resolved_parameter_annotation(
    parameter: inspect.Parameter,
    resolved_annotations: Dict[str, Any],
) -> Any:
    return resolved_annotations.get(parameter.name, parameter.annotation)


def _resolve_callback_annotations(callback: Callable[..., Any]) -> Dict[str, Any]:
    globalns = getattr(callback, "__globals__", None)
    try:
        return get_type_hints(callback, globalns=globalns, include_extras=True)
    except TypeError:
        try:
            return get_type_hints(callback, globalns=globalns)
        except Exception:  # noqa: BLE001
            return {}
    except Exception:  # noqa: BLE001
        return {}


def _supports_parameter(parameter: inspect.Parameter, annotation: Any) -> bool:
    name = parameter.name

    if _annotation_includes(annotation, HandlerContext):
        return True
    if _annotation_includes(annotation, FSMContext):
        return True
    if _annotation_includes(annotation, Message):
        return True
    if _annotation_includes(annotation, Callback):
        return True
    if _annotation_includes(annotation, Update):
        return True
    if _annotation_includes_subclass(annotation, MaxBaseModel):
        return True
    if annotation is Any:
        return True
    if name in ("state", "update_type") and _annotation_includes(annotation, str):
        return True
    if name in ("chat_id", "user_id") and _annotation_includes(annotation, int):
        return True
    if annotation is inspect.Parameter.empty:
        return name in (
            "context",
            "fsm",
            "fsm_context",
            "state",
            "update",
            "message",
            "callback",
            "chat_id",
            "user_id",
            "update_type",
        )
    return False


def _resolve_parameter_value(
    parameter: inspect.Parameter,
    context: HandlerContext,
    annotation: Any,
) -> Tuple[Any, bool]:
    name = parameter.name

    if _annotation_includes(annotation, HandlerContext):
        return context, True
    if _annotation_includes(annotation, FSMContext):
        return context.fsm, context.fsm is not None or _annotation_is_optional(annotation)
    if _annotation_includes(annotation, Message):
        value = _extract_message(context.update)
        return value, value is not None or _annotation_is_optional(annotation)
    if _annotation_includes(annotation, Callback):
        value = _extract_callback(context.update)
        return value, value is not None or _annotation_is_optional(annotation)
    if _annotation_includes(annotation, Update) or _annotation_includes_subclass(annotation, MaxBaseModel):
        return _coerce_update_by_annotation(context.update, annotation), True
    if annotation is Any:
        return context.update, True

    if name == "context":
        return context, True
    if name in ("fsm", "fsm_context"):
        return context.fsm, context.fsm is not None
    if name == "state":
        return context.state, True
    if name == "update":
        return context.update, True
    if name == "message":
        value = _extract_message(context.update)
        return value, value is not None
    if name == "callback":
        value = _extract_callback(context.update)
        return value, value is not None
    if name == "chat_id":
        value = _extract_chat_id(context.update)
        return value, value is not None
    if name == "user_id":
        value = _extract_user_id(context.update)
        return value, value is not None
    if name == "update_type":
        value = _extract_update_type(context.update)
        return value, value is not None

    if annotation is inspect.Parameter.empty:
        return None, False
    if _annotation_includes(annotation, str) and name in ("state", "update_type"):
        if name == "state":
            return context.state, context.state is not None or _annotation_is_optional(annotation)
        value = _extract_update_type(context.update)
        return value, value is not None or _annotation_is_optional(annotation)
    if _annotation_includes(annotation, int) and name in ("chat_id", "user_id"):
        if name == "chat_id":
            value = _extract_chat_id(context.update)
        else:
            value = _extract_user_id(context.update)
        return value, value is not None or _annotation_is_optional(annotation)

    return None, False


def _coerce_update_by_annotation(update: Any, annotation: Any) -> Any:
    if annotation in (inspect.Parameter.empty, Any):
        return update
    if isinstance(update, dict):
        klass = _first_model_annotation(annotation)
        if klass is not None:
            try:
                return klass.model_validate(update)
            except Exception:  # noqa: BLE001
                return update
    return update


def _first_model_annotation(annotation: Any) -> Optional[Any]:
    annotation = _unwrap_annotation(annotation)
    if _is_model_class(annotation):
        return annotation
    origin = get_origin(annotation)
    if origin is Union:
        for option in get_args(annotation):
            option = _unwrap_annotation(option)
            if _is_model_class(option):
                return option
    return None


def _is_model_class(value: Any) -> bool:
    return isinstance(value, type) and issubclass(value, MaxBaseModel)


def _annotation_includes(annotation: Any, klass: Any) -> bool:
    annotation = _unwrap_annotation(annotation)
    if annotation is inspect.Parameter.empty:
        return False
    if annotation is Any:
        return False
    if annotation == klass:
        return True
    origin = get_origin(annotation)
    if origin is Union:
        return any(_unwrap_annotation(option) == klass for option in get_args(annotation))
    return False


def _annotation_includes_subclass(annotation: Any, base_class: Any) -> bool:
    annotation = _unwrap_annotation(annotation)
    if isinstance(annotation, type) and issubclass(annotation, base_class):
        return True
    origin = get_origin(annotation)
    if origin is Union:
        for option in get_args(annotation):
            option = _unwrap_annotation(option)
            if isinstance(option, type) and issubclass(option, base_class):
                return True
    return False


def _annotation_is_optional(annotation: Any) -> bool:
    annotation = _unwrap_annotation(annotation)
    origin = get_origin(annotation)
    if origin is not Union:
        return False
    return any(_unwrap_annotation(option) is type(None) for option in get_args(annotation))


def _unwrap_annotation(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        if args:
            return _unwrap_annotation(args[0])
    return annotation


def _extract_update_type(update: Any) -> Optional[str]:
    value = getattr(update, "update_type", None)
    if isinstance(update, dict):
        value = update.get("update_type")
    if value is None:
        return None
    return str(value)


def _extract_message(update: Any) -> Optional[Message]:
    raw = getattr(update, "message", None)
    if isinstance(update, dict):
        raw = update.get("message")
    return _coerce_model(raw, Message)


def _extract_callback(update: Any) -> Optional[Callback]:
    raw = getattr(update, "callback", None)
    if isinstance(update, dict):
        raw = update.get("callback")
    callback = _coerce_model(raw, Callback)
    if callback is None:
        return None
    # Safely handle potential dict or foreign object from _coerce_model
    if getattr(callback, "message", None) is None:
        message = _extract_message(update)
        if message is not None:
            try:
                callback.message = message
            except (AttributeError, TypeError):
                # Cannot set attribute on dict or immutable object
                if isinstance(callback, dict) and "message" not in callback:
                    callback["message"] = message
    return callback


def _extract_chat_id(update: Any) -> Optional[int]:
    direct = getattr(update, "chat_id", None)
    if isinstance(update, dict):
        direct = update.get("chat_id")
    if direct is not None:
        return _to_int(direct)

    message = _extract_message(update)
    if message is not None:
        chat = getattr(message, "chat", None)
        if chat is not None:
            return _to_int(getattr(chat, "chat_id", None))
        if isinstance(message, dict):
            chat_dict = message.get("chat")
            if isinstance(chat_dict, dict):
                return _to_int(chat_dict.get("chat_id"))

    chat = getattr(update, "chat", None)
    if isinstance(update, dict):
        chat = update.get("chat")
    chat_dict = _as_dict(chat)
    if chat_dict:
        return _to_int(chat_dict.get("chat_id"))
    return None


def _extract_user_id(update: Any) -> Optional[int]:
    direct = getattr(update, "user_id", None)
    if isinstance(update, dict):
        direct = update.get("user_id")
    if direct is not None:
        return _to_int(direct)

    user = getattr(update, "user", None)
    if isinstance(update, dict):
        user = update.get("user")
    user_dict = _as_dict(user)
    if user_dict:
        direct_user = _to_int(user_dict.get("user_id"))
        if direct_user is not None:
            return direct_user

    message = _extract_message(update)
    if message is not None:
        sender = getattr(message, "sender", None)
        sender_dict = _as_dict(sender)
        if not sender_dict and isinstance(message, dict):
            sender_dict = _as_dict(message.get("sender"))
        if sender_dict:
            sender_id = _to_int(sender_dict.get("user_id"))
            if sender_id is not None:
                return sender_id

    callback = _extract_callback(update)
    if callback is not None:
        user_field = getattr(callback, "user", None)
        callback_user = _as_dict(user_field)
        if not callback_user and isinstance(callback, dict):
            callback_user = _as_dict(callback.get("user"))
        if callback_user:
            callback_user_id = _to_int(callback_user.get("user_id"))
            if callback_user_id is not None:
                return callback_user_id
    return None


def _coerce_model(value: Any, klass: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, klass):
        return value
    if isinstance(value, dict):
        try:
            return klass.model_validate(value)
        except Exception:  # noqa: BLE001
            pass  # Fall through to return value
    elif hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump(by_alias=True)
            if isinstance(dumped, dict):
                return klass.model_validate(dumped)
        except Exception:  # noqa: BLE001
            pass  # Fall through to return value
    return value


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(by_alias=True)
        if isinstance(dumped, dict):
            return dumped
    return {}


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
