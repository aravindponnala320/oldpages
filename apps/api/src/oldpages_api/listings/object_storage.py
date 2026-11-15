"""Minimal S3-compatible helpers (MinIO locally) using AWS Signature V4 presigned URLs."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from urllib.parse import quote, urlparse

import httpx

from oldpages_api.core.config import Settings


def presigned_url(
    settings: Settings,
    method: str,
    storage_key: str,
    *,
    endpoint: str,
    expires_seconds: int = 900,
) -> str:
    endpoint = endpoint.rstrip("/")
    host = urlparse(endpoint).netloc
    path = "/" + quote(f"{settings.object_storage_bucket}/{storage_key}", safe="/-_.~")
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    scope = f"{now:%Y%m%d}/{settings.object_storage_region}/s3/aws4_request"
    query = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{settings.object_storage_access_key}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires_seconds),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_query = "&".join(
        f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in sorted(query.items())
    )
    canonical_request = "\n".join(
        [method, path, canonical_query, f"host:{host}\n", "host", "UNSIGNED-PAYLOAD"]
    )
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )
    key = f"AWS4{settings.object_storage_secret_key.get_secret_value()}".encode()
    for part in (f"{now:%Y%m%d}", settings.object_storage_region, "s3", "aws4_request"):
        key = hmac.new(key, part.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    return f"{endpoint}{path}?{canonical_query}&X-Amz-Signature={signature}"


def public_object_url(settings: Settings, storage_key: str) -> str:
    base = (settings.object_storage_public_endpoint or settings.object_storage_endpoint).rstrip("/")
    return f"{base}/{quote(f'{settings.object_storage_bucket}/{storage_key}', safe='/-_.~')}"


async def object_exists(settings: Settings, storage_key: str) -> bool:
    url = presigned_url(settings, "HEAD", storage_key, endpoint=settings.object_storage_endpoint)
    async with httpx.AsyncClient(timeout=10.0) as http:
        response = await http.head(url)
    return response.status_code == 200


async def read_object(settings: Settings, storage_key: str, *, max_bytes: int) -> bytes | None:
    """The stored bytes, or None when missing. Raises ValueError past max_bytes."""
    url = presigned_url(settings, "GET", storage_key, endpoint=settings.object_storage_endpoint)
    async with httpx.AsyncClient(timeout=30.0) as http, http.stream("GET", url) as response:
        if response.status_code == 404:
            return None
        response.raise_for_status()
        chunks: list[bytes] = []
        size = 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("object too large")
            chunks.append(chunk)
    return b"".join(chunks)


async def write_object(
    settings: Settings, storage_key: str, data: bytes, content_type: str
) -> None:
    url = presigned_url(settings, "PUT", storage_key, endpoint=settings.object_storage_endpoint)
    async with httpx.AsyncClient(timeout=30.0) as http:
        response = await http.put(url, content=data, headers={"Content-Type": content_type})
    response.raise_for_status()


async def delete_object(settings: Settings, storage_key: str) -> None:
    url = presigned_url(settings, "DELETE", storage_key, endpoint=settings.object_storage_endpoint)
    async with httpx.AsyncClient(timeout=10.0) as http:
        await http.delete(url)
