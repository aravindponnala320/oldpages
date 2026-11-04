"""Shared async HTTP client for outbound geo calls (Nominatim, etc.)."""

from __future__ import annotations

from typing import Any

_client: Any | None = None


def get_http_client() -> Any:
    global _client
    if _client is None:
        try:
            import httpx  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - httpx is a dev/prod dep
            raise RuntimeError(
                "httpx is required for outbound geo calls. Add httpx to project deps."
            ) from exc
        _client = httpx.AsyncClient()
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        finally:
            _client = None


def set_http_client(client: Any | None) -> None:
    """Test/DI hook to inject a mock httpx client."""
    global _client
    _client = client
