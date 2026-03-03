from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from ..fsm import create_fsm_context_from_update
from ..fsm.storage import BaseStorage
from .context import HandlerContext
from .di import invoke_handler, validate_handler_signature

FilterCallable = Callable[[Any], Any]
HandlerCallable = Callable[..., Any]
BeforeHookCallable = Callable[[Any], Any]
AfterHookCallable = Callable[[Any, bool], Any]
ErrorHookCallable = Callable[[Any, Exception], Any]
ErrorHandlerCallable = Callable[[Any, Exception], Any]

logger = logging.getLogger(__name__)


@dataclass
class _HandlerRecord:
    callback: HandlerCallable
    update_type: Optional[str]
    filters: List[FilterCallable]
    state: Optional[str]


class Router:
    def __init__(self, storage: Optional[BaseStorage] = None) -> None:
        self._handlers: List[_HandlerRecord] = []
        self._children: List["Router"] = []
        self._parent: Optional["Router"] = None
        self._before_hooks: List[BeforeHookCallable] = []
        self._after_hooks: List[AfterHookCallable] = []
        self._error_hooks: List[ErrorHookCallable] = []
        self._error_handlers: List[ErrorHandlerCallable] = []
        self._storage: Optional[BaseStorage] = storage

    @property
    def storage(self) -> Optional[BaseStorage]:
        return self._storage

    def set_storage(self, storage: Optional[BaseStorage]) -> None:
        self._storage = storage
        for child in self._children:
            if child.storage is None:
                child.set_storage(storage)

    def include_router(self, router: "Router") -> None:
        router._parent = self
        if router.storage is None:
            router.set_storage(self._storage)
        self._children.append(router)

    def include_routers(self, *routers: "Router") -> None:
        for router in routers:
            self.include_router(router)

    def register(
        self,
        callback: HandlerCallable,
        update_type: Optional[str] = None,
        filters: Optional[List[FilterCallable]] = None,
        state: Optional[str] = None,
    ) -> HandlerCallable:
        validate_handler_signature(callback)
        self._handlers.append(
            _HandlerRecord(
                callback=callback,
                update_type=update_type,
                filters=filters or [],
                state=state,
            )
        )
        return callback

    def on_update(
        self,
        update_type: Optional[str] = None,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        def _decorator(callback: HandlerCallable) -> HandlerCallable:
            self.register(callback, update_type=update_type, filters=list(filters), state=state)
            return callback

        return _decorator

    def message(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.message_created(*filters, state=state)

    def callback_query(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.message_callback(*filters, state=state)

    def message_created(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_created", *filters, state=state)

    def message_callback(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_callback", *filters, state=state)

    def message_edited(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_edited", *filters, state=state)

    def message_removed(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_removed", *filters, state=state)

    def bot_added(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("bot_added", *filters, state=state)

    def bot_removed(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("bot_removed", *filters, state=state)

    def user_added(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("user_added", *filters, state=state)

    def user_removed(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("user_removed", *filters, state=state)

    def bot_started(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("bot_started", *filters, state=state)

    def bot_stopped(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("bot_stopped", *filters, state=state)

    def chat_title_changed(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("chat_title_changed", *filters, state=state)

    def message_chat_created(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("message_chat_created", *filters, state=state)

    def dialog_muted(self, *filters: FilterCallable, state: Optional[str] = None) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("dialog_muted", *filters, state=state)

    def dialog_unmuted(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("dialog_unmuted", *filters, state=state)

    def dialog_cleared(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("dialog_cleared", *filters, state=state)

    def dialog_removed(
        self,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Callable[[HandlerCallable], HandlerCallable]:
        return self.on_update("dialog_removed", *filters, state=state)

    def middleware_before(
        self,
        callback: Optional[BeforeHookCallable] = None,
    ) -> Any:
        return self._register_callback(self._before_hooks, callback)

    def middleware_after(
        self,
        callback: Optional[AfterHookCallable] = None,
    ) -> Any:
        return self._register_callback(self._after_hooks, callback)

    def middleware_error(
        self,
        callback: Optional[ErrorHookCallable] = None,
    ) -> Any:
        return self._register_callback(self._error_hooks, callback)

    def on_error(
        self,
        callback: Optional[ErrorHandlerCallable] = None,
    ) -> Any:
        return self._register_callback(self._error_handlers, callback)

    async def dispatch(self, update: Any) -> bool:
        handled = False
        try:
            if not await self._run_before_hooks(update):
                return False

            fsm_context = None
            current_state = None
            if self._storage is not None:
                fsm_context = create_fsm_context_from_update(self._storage, update)
                if fsm_context is not None:
                    current_state = await fsm_context.get_state()
            handler_context = HandlerContext(
                update=update,
                router=self,
                storage=self._storage,
                fsm=fsm_context,
                state=current_state,
            )

            for handler in self._handlers:
                if not _match_update_type(update, handler.update_type):
                    continue
                if handler.state is not None and handler_context.state != handler.state:
                    continue
                try:
                    if not await _passes_filters(update, handler.filters):
                        continue
                    await invoke_handler(handler.callback, handler_context)
                    handled = True
                except Exception as exc:  # noqa: BLE001
                    await self._emit_error(update, exc)

            for child in self._children:
                child_handled = await child.dispatch(update)
                handled = handled or child_handled

            return handled
        finally:
            await self._run_after_hooks(update, handled)

    def _register_callback(self, store: List[Any], callback: Optional[Any]) -> Any:
        if callback is not None:
            store.append(callback)
            return callback

        def _decorator(func: Any) -> Any:
            store.append(func)
            return func

        return _decorator

    async def _run_before_hooks(self, update: Any) -> bool:
        for hook in self._before_hooks:
            try:
                await _resolve_result(hook(update))
            except Exception as exc:  # noqa: BLE001
                await self._emit_error(update, exc)
                return False
        return True

    async def _run_after_hooks(self, update: Any, handled: bool) -> None:
        for hook in self._after_hooks:
            try:
                await _resolve_result(hook(update, handled))
            except Exception as exc:  # noqa: BLE001
                await self._emit_error(update, exc)

    async def _emit_error(self, update: Any, error: Exception) -> None:
        chain = self._iter_error_chain()
        has_error_consumers = False
        for router in chain:
            has_error_consumers = has_error_consumers or bool(router._error_hooks or router._error_handlers)
            await router._run_error_hooks(update, error)
            await router._run_error_handlers(update, error)

        if not has_error_consumers:
            logger.exception("Unhandled dispatcher error", exc_info=error)

    async def _run_error_hooks(self, update: Any, error: Exception) -> None:
        for hook in self._error_hooks:
            try:
                await _resolve_result(hook(update, error))
            except Exception:  # noqa: BLE001
                logger.exception("Dispatcher middleware_error hook failed")

    async def _run_error_handlers(self, update: Any, error: Exception) -> None:
        for handler in self._error_handlers:
            try:
                await _resolve_result(handler(update, error))
            except Exception:  # noqa: BLE001
                logger.exception("Dispatcher on_error handler failed")

    def _iter_error_chain(self) -> List["Router"]:
        chain: List["Router"] = []
        current: Optional["Router"] = self
        while current is not None:
            chain.append(current)
            current = current._parent
        return chain


def _extract_update_type(update: Any) -> Optional[str]:
    if isinstance(update, dict):
        value = update.get("update_type")
    else:
        value = getattr(update, "update_type", None)
    if value is None:
        return None
    return str(value)


def _match_update_type(update: Any, expected: Optional[str]) -> bool:
    if expected is None:
        return True
    return _extract_update_type(update) == expected


async def _passes_filters(update: Any, filters: List[FilterCallable]) -> bool:
    for filter_func in filters:
        result = await _resolve_result(filter_func(update))
        if not bool(result):
            return False
    return True


async def _resolve_result(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value
