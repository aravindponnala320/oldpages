"""Checks an uploaded photo really is an image and re-encodes it without metadata.

The presigned PUT only signs the host, so the uploader controls the bytes, size and type.
Re-encoding drops EXIF (GPS position, camera serial), XMP and anything appended to the file.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_EDGE = 2560

_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class InvalidImageError(ValueError):
    pass


@dataclass(frozen=True)
class CleanImage:
    data: bytes
    content_type: str
    width: int
    height: int


def sanitize_image(data: bytes) -> CleanImage:
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImageError("Photos can be at most 15 MB.")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format or ""
            if fmt not in _FORMATS:
                raise InvalidImageError("Upload a JPEG, PNG or WebP photo.")
            if probe.width * probe.height > MAX_PIXELS:
                raise InvalidImageError("This photo is too large. Use one under 40 megapixels.")
            probe.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            upright = ImageOps.exif_transpose(image)  # keep the photo upright once EXIF is gone
            upright.thumbnail((MAX_EDGE, MAX_EDGE))
            out = io.BytesIO()
            if fmt == "JPEG":
                upright.convert("RGB").save(out, "JPEG", quality=85, optimize=True)
            elif fmt == "PNG":
                upright.save(out, "PNG", optimize=True)
            else:
                upright.save(out, "WEBP", quality=85)
            return CleanImage(out.getvalue(), _FORMATS[fmt], upright.width, upright.height)
    except InvalidImageError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombError,
    ) as error:
        raise InvalidImageError("This file isn't a photo we can read.") from error
