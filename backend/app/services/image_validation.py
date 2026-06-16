import io
import logging

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


async def validate_image_upload(file: UploadFile) -> tuple[bytes, Image.Image]:
    settings = get_settings()

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if len(content) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes / (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_mb:.0f}MB")

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file") from e

    if _is_blank_canvas(image):
        raise HTTPException(
            status_code=400,
            detail="Canvas appears blank. Please draw something before submitting.",
        )

    return content, image


def _is_blank_canvas(image: Image.Image, threshold: float = 0.98) -> bool:
    """Detect mostly white/blank canvases."""
    rgb = image.convert("RGB").resize((100, 100))
    pixels = list(rgb.getdata())
    white_count = sum(1 for r, g, b in pixels if r > 240 and g > 240 and b > 240)
    return white_count / len(pixels) >= threshold
