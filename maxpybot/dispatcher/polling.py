from __future__ import annotations

import inspect
from typing import Any, Callable, List, Optional

from ..api_client import MaxBot
from .router import Router

LifecycleHookCallable = Callable[[], Any]


class PollingRunner:
    def __init__(self, api: MaxBot, router: Router) -> None:
        self._api = api
        self._router = router
        self._running = False
        self._start_hooks: List[LifecycleHookCallable] = []
        self._stop_hooks: List[LifecycleHookCallable] = []
        self._shutdown_hooks: List[LifecycleHookCallable] = []

    @property
    def running(self) -> bool:
        return self._running

    def on_start(self, callback: Optional[LifecycleHookCallable] = None) -> Any:
        return self._register_hook(self._start_hooks, callback)

    def on_stop(self, callback: Optional[LifecycleHookCallable] = None) -> Any:
        return self._register_hook(self._stop_hooks, callback)

    def on_shutdown(self, callback: Optional[LifecycleHookCallable] = None) -> Any:
        return self._register_hook(self._shutdown_hooks, callback)

    def stop(self) -> None:
        self._running = False

    async def run(self, marker: Optional[int] = None, types: Optional[List[str]] = None) -> None:
        self._running = True
        try:
            await self._run_hooks(self._start_hooks)
            async for update in self._api.iter_updates(marker=marker, types=types):
                if not self._running:
                    break
                await self._router.dispatch(update)
                if not self._running:
                    break
        finally:
            self._running = False
            await self._run_hooks(self._stop_hooks)
            await self._run_hooks(self._shutdown_hooks)

    def _register_hook(self, store: List[LifecycleHookCallable], callback: Optional[LifecycleHookCallable]) -> Any:
        if callback is not None:
            store.append(callback)
            return callback

        def _decorator(func: LifecycleHookCallable) -> LifecycleHookCallable:
            store.append(func)
            return func

        return _decorator

    async def _run_hooks(self, hooks: List[LifecycleHookCallable]) -> None:
        for hook in hooks:
            result = hook()
            if inspect.isawaitable(result):
                await result
