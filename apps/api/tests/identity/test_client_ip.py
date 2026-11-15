from __future__ import annotations

from types import SimpleNamespace

from starlette.requests import Request

from oldpages_api.core.config import Settings
from oldpages_api.identity.dependencies import client_ip


def request(settings: Settings, headers: dict[str, str]) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(settings=settings))
    return Request(
        {
            "type": "http",
            "app": app,
            "client": ("172.16.0.9", 443),  # the hosting proxy
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }
    )


def test_uses_the_header_the_host_overwrites() -> None:
    on_fly = Settings(environment="test", client_ip_header="Fly-Client-IP")
    spoofed = {"X-Forwarded-For": "1.2.3.4", "Fly-Client-IP": "203.0.113.7"}

    assert client_ip(request(on_fly, spoofed)) == "203.0.113.7"


def test_never_trusts_forwarded_for_without_a_configured_header() -> None:
    plain = Settings(environment="test")

    assert client_ip(request(plain, {"X-Forwarded-For": "1.2.3.4"})) == "172.16.0.9"
    assert client_ip(request(plain, {"Fly-Client-IP": "1.2.3.4"})) == "172.16.0.9"
