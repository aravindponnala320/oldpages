from __future__ import annotations

import io

import pytest
from httpx import AsyncClient
from PIL import Image

from conftest import RegisterUser
from helpers import auth
from oldpages_api.listings.images import InvalidImageError, sanitize_image


def photo_with_gps() -> bytes:
    image = Image.new("RGB", (40, 20), "red")
    exif = Image.Exif()
    exif[0x0110] = "Secret Phone"  # camera model
    exif[0x0112] = 6  # rotated 90°
    exif.get_ifd(0x8825)[2] = (17.0, 26.0, 0.0)  # GPS latitude
    out = io.BytesIO()
    image.save(out, "JPEG", exif=exif.tobytes())
    return out.getvalue()


def test_sanitize_strips_metadata_and_keeps_orientation() -> None:
    clean = sanitize_image(photo_with_gps())

    with Image.open(io.BytesIO(clean.data)) as result:
        assert dict(result.getexif()) == {}
        assert result.size == (20, 40)  # turned upright before EXIF was dropped
    assert b"Secret Phone" not in clean.data
    assert clean.content_type == "image/jpeg"


@pytest.mark.parametrize(
    "data",
    [b"<?php system($_GET['c']); ?>", b"\xff\xd8\xff\xe0 truncated jpeg", b""],
)
def test_sanitize_rejects_files_that_are_not_images(data: bytes) -> None:
    with pytest.raises(InvalidImageError):
        sanitize_image(data)


def test_sanitize_rejects_gif_even_though_it_is_an_image() -> None:
    out = io.BytesIO()
    Image.new("RGB", (4, 4)).save(out, "GIF")
    with pytest.raises(InvalidImageError):
        sanitize_image(out.getvalue())


async def start_upload(client: AsyncClient, token: str) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 2048, "content_type": "image/jpeg", "filename": "a.jpg"},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"], response.json()["storage_key"]


@pytest.mark.asyncio
async def test_completed_upload_is_rewritten_without_exif(
    client: AsyncClient,
    register_user: RegisterUser,
    stub_object_storage: dict[str, bytes],
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    media_id, key = await start_upload(client, token)
    stub_object_storage[key] = photo_with_gps()

    response = await client.post(f"/api/v1/media/{media_id}/complete", headers=auth(token), json={})

    assert response.status_code == 200, response.text
    assert b"Secret Phone" not in stub_object_storage[key]
    assert response.json()["byte_size"] == len(stub_object_storage[key])


@pytest.mark.asyncio
async def test_completed_upload_that_is_not_an_image_is_rejected_and_deleted(
    client: AsyncClient,
    register_user: RegisterUser,
    stub_object_storage: dict[str, bytes],
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    media_id, key = await start_upload(client, token)
    stub_object_storage[key] = b"<html><script>alert(1)</script></html>"

    response = await client.post(f"/api/v1/media/{media_id}/complete", headers=auth(token), json={})

    assert response.status_code == 422, response.text
    assert key not in stub_object_storage
    again = await client.post(f"/api/v1/media/{media_id}/complete", headers=auth(token), json={})
    assert again.status_code == 422  # a rejected upload can't be retried into "approved"
