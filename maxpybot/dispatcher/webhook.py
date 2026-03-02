from __future__ import annotations

from aiohttp import web

from ..compat.update_parser import UpdateParser
from .router import Router


class WebhookHandler:
    def __init__(self, router: Router) -> None:
        self._router = router
        self._parser = UpdateParser(debug=False)

    async def handle(self, request: web.Request) -> web.StreamResponse:
        if request.method.upper() != "POST":
            return web.Response(status=405, text="Method not allowed")

        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            return web.Response(status=400, text="Invalid JSON")

        if not isinstance(payload, dict):
            return web.Response(status=400, text="Invalid payload")

        update = self._parser.parse_update(payload)
        await self._router.dispatch(update)
        return web.Response(status=200, text="OK")
