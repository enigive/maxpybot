from __future__ import annotations

from typing import Any, List, Optional

from ..api_client import MaxBot
from ..fsm.storage import BaseStorage
from .router import (
    AfterHookCallable,
    BeforeHookCallable,
    ErrorHandlerCallable,
    ErrorHookCallable,
    FilterCallable,
    HandlerCallable,
    Router,
)
from .webhook import WEBHOOK_SECRET_HEADER, WebhookMetrics


class Dispatcher:
    """High-level dispatcher to combine multiple routers."""

    def __init__(self, storage: Optional[BaseStorage] = None) -> None:
        self._router = Router(storage=storage)

    @property
    def router(self) -> Router:
        return self._router

    def include_router(self, router: Router) -> None:
        self._router.include_router(router)

    def include_routers(self, *routers: Router) -> None:
        self._router.include_routers(*routers)

    def set_storage(self, storage: Optional[BaseStorage]) -> None:
        self._router.set_storage(storage)

    def on_update(
        self,
        update_type: Optional[str] = None,
        *filters: FilterCallable,
        state: Optional[str] = None
    ) -> Any:
        return self._router.on_update(update_type, *filters, state=state)

    def message(self, *filters: FilterCallable, state: Optional[str] = None) -> Any:
        return self._router.message(*filters, state=state)

    def callback_query(self, *filters: FilterCallable, state: Optional[str] = None) -> Any:
        return self._router.callback_query(*filters, state=state)

    def middleware_before(self, callback: Optional[BeforeHookCallable] = None) -> Any:
        return self._router.middleware_before(callback)

    def middleware_after(self, callback: Optional[AfterHookCallable] = None) -> Any:
        return self._router.middleware_after(callback)

    def middleware_error(self, callback: Optional[ErrorHookCallable] = None) -> Any:
        return self._router.middleware_error(callback)

    def on_error(self, callback: Optional[ErrorHandlerCallable] = None) -> Any:
        return self._router.on_error(callback)

    async def dispatch(self, update: Any) -> bool:
        return await self._router.dispatch(update)

    async def start_polling(
        self,
        bot: MaxBot,
        marker: Optional[int] = None,
        types: Optional[List[str]] = None,
    ) -> None:
        await bot.start_polling(router=self._router, marker=marker, types=types)

    def start_webhook(
        self,
        bot: MaxBot,
        path: str,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_path: str = "",
        key_path: str = "",
        secret: str = "",
        secret_header: str = WEBHOOK_SECRET_HEADER,
        allowed_ip_networks: Optional[List[str]] = None,
        max_processing_retries: int = 0,
        metrics: Optional[WebhookMetrics] = None,
        subscribe_url: str = "",
        update_types: Optional[List[str]] = None,
        unsubscribe_on_shutdown: bool = False,
    ) -> None:
        bot.start_webhook(
            router=self._router,
            path=path,
            host=host,
            port=port,
            cert_path=cert_path,
            key_path=key_path,
            secret=secret,
            secret_header=secret_header,
            allowed_ip_networks=allowed_ip_networks,
            max_processing_retries=max_processing_retries,
            metrics=metrics,
            subscribe_url=subscribe_url,
            update_types=update_types,
            unsubscribe_on_shutdown=unsubscribe_on_shutdown,
        )

    def register(
        self,
        callback: HandlerCallable,
        update_type: Optional[str] = None,
        filters: Optional[List[FilterCallable]] = None,
        state: Optional[str] = None,
    ) -> HandlerCallable:
        return self._router.register(
            callback=callback,
            update_type=update_type,
            filters=filters,
            state=state,
        )
