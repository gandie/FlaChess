import base64
from binascii import Error as Base64Error
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

AVATAR_MAX_INPUT_BYTES = 5 * 1024 * 1024
AVATAR_SIZE = (200, 200)
SUPPORTED_AVATAR_FORMATS = {"JPEG", "PNG", "WEBP"}
SUPPORTED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


def normalize_avatar(avatar: str | None) -> str | None:
    if avatar is None:
        return None
    try:
        header, encoded = avatar.split(",", 1)
    except ValueError as error:
        raise ValueError("avatar must be a Base64 image data URI") from error
    metadata, separator, encoding = header.partition(";")
    if (
        not metadata.startswith("data:")
        or separator != ";"
        or encoding.lower() != "base64"
        or metadata.removeprefix("data:") not in SUPPORTED_AVATAR_TYPES
    ):
        raise ValueError("avatar must be a PNG, JPEG, or WebP Base64 image")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (Base64Error, ValueError) as error:
        raise ValueError("avatar contains invalid Base64 data") from error
    if not image_bytes:
        raise ValueError("avatar image cannot be empty")
    if len(image_bytes) > AVATAR_MAX_INPUT_BYTES:
        raise ValueError("avatar image must be 5 MB or smaller")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.format not in SUPPORTED_AVATAR_FORMATS:
                raise ValueError("avatar must be a PNG, JPEG, or WebP image")
            source.load()
            normalized = ImageOps.fit(
                ImageOps.exif_transpose(source).convert("RGBA"),
                AVATAR_SIZE,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
    except UnidentifiedImageError as error:
        raise ValueError("avatar must be a valid PNG, JPEG, or WebP image") from error
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError("avatar image could not be processed") from error

    output = BytesIO()
    normalized.save(output, format="PNG", optimize=True)
    encoded_avatar = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded_avatar}"
