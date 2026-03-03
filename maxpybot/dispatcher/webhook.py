from __future__ import annotations

import logging
import ssl
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network
from typing import List, Mapping, Optional, Union

from aiohttp import web

from ..compat.update_parser import UpdateParser
from .router import Router

WEBHOOK_SECRET_HEADER = "X-Max-Bot-Api-Secret"
IPNetwork = Union[IPv4Network, IPv6Network]
IPAddress = Union[IPv4Address, IPv6Address]
logger = logging.getLogger(__name__)


@dataclass
class WebhookMetrics:
    requests_total: int = 0
    rejected_secret_total: int = 0
    rejected_ip_total: int = 0
    invalid_json_total: int = 0
    invalid_payload_total: int = 0
    processed_total: int = 0
    retried_total: int = 0
    failed_total: int = 0


class WebhookHandler:
    def __init__(
        self,
        router: Router,
        bot: Optional[MaxBot] = None,
        secret: str = "",
        secret_header: str = WEBHOOK_SECRET_HEADER,
        allowed_ip_networks: Optional[List[str]] = None,
        max_processing_retries: int = 0,
        metrics: Optional[WebhookMetrics] = None,
    ) -> None:
        self._router = router
        self._bot = bot
        self._parser = UpdateParser(debug=False)
        self._secret = secret
        self._secret_header = secret_header
        self._allowed_ip_networks = self._parse_ip_networks(allowed_ip_networks or [])
        self._max_processing_retries = max(0, int(max_processing_retries))
        self._metrics = metrics or WebhookMetrics()

    @property
    def metrics(self) -> WebhookMetrics:
        return self._metrics

    async def handle(self, request: web.Request) -> web.StreamResponse:
        self._metrics.requests_total += 1

        if request.method.upper() != "POST":
            return web.Response(status=405, text="Method not allowed")

        if self._secret and not self._is_valid_secret(getattr(request, "headers", {})):
            self._metrics.rejected_secret_total += 1
            logger.warning("Webhook request rejected due to invalid secret")
            return web.Response(status=403, text="Invalid webhook secret")
        if self._allowed_ip_networks and not self._is_allowed_ip(self._extract_client_ip(request)):
            self._metrics.rejected_ip_total += 1
            logger.warning("Webhook request rejected by IP allowlist")
            return web.Response(status=403, text="Forbidden IP")

        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            self._metrics.invalid_json_total += 1
            logger.warning("Webhook request rejected due to invalid JSON")
            return web.Response(status=400, text="Invalid JSON")

        if not isinstance(payload, dict):
            self._metrics.invalid_payload_total += 1
            logger.warning("Webhook request rejected due to invalid payload type")
            return web.Response(status=400, text="Invalid payload")

        attempt = 0
        while True:
            try:
                update = self._parser.parse_update(payload, bot=self._bot)
                await self._router.dispatch(update)
                self._metrics.processed_total += 1
                if attempt > 0:
                    logger.info("Webhook request processed after retry")
                return web.Response(status=200, text="OK")
            except Exception as exc:  # noqa: BLE001
                if attempt >= self._max_processing_retries:
                    self._metrics.failed_total += 1
                    logger.exception("Webhook processing failed", exc_info=exc)
                    return web.Response(status=500, text="Webhook processing failed")
                attempt += 1
                self._metrics.retried_total += 1
                logger.warning(
                    "Webhook processing failed, retry %s/%s",
                    attempt,
                    self._max_processing_retries,
                    exc_info=exc,
                )

    def _is_valid_secret(self, headers: Mapping[str, str]) -> bool:
        received = headers.get(self._secret_header, "")
        return received == self._secret

    def _parse_ip_networks(self, values: List[str]) -> List[IPNetwork]:
        parsed: List[IPNetwork] = []
        for raw_value in values:
            value = str(raw_value or "").strip()
            if not value:
                continue
            parsed.append(ip_network(value, strict=False))
        return parsed

    def _extract_client_ip(self, request: web.Request) -> str:
        value = str(getattr(request, "remote", "") or "").strip()
        if "%" in value:
            return value.split("%", 1)[0]
        return value

    def _is_allowed_ip(self, value: str) -> bool:
        if not value:
            return False
        try:
            client_ip: IPAddress = ip_address(value)
        except ValueError:
            return False
        for network in self._allowed_ip_networks:
            if client_ip in network:
                return True
        return False


WEBHOOK_HANDLER_APP_KEY = web.AppKey("maxpybot.webhook_handler", WebhookHandler)


def create_webhook_app(
    router: Router,
    path: str,
    bot: Optional[MaxBot] = None,
    secret: str = "",
    secret_header: str = WEBHOOK_SECRET_HEADER,
    allowed_ip_networks: Optional[List[str]] = None,
    max_processing_retries: int = 0,
    metrics: Optional[WebhookMetrics] = None,
) -> web.Application:
    app = web.Application()
    handler = WebhookHandler(
        router=router,
        bot=bot,
        secret=secret,
        secret_header=secret_header,
        allowed_ip_networks=allowed_ip_networks,
        max_processing_retries=max_processing_retries,
        metrics=metrics,
    )
    app[WEBHOOK_HANDLER_APP_KEY] = handler
    app.router.add_post(path, handler.handle)
    return app


def create_https_ssl_context(cert_path: str, key_path: str) -> ssl.SSLContext:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_path, key_path)
    return context
