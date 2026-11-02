from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError


class InvalidImageError(ValueError):
    """The image cannot be decoded by the detectors."""


class ImageTooLargeError(ValueError):
    """The image exceeds the allowed pixel count."""


def validate_image(path: Path, *, max_pixels: int) -> None:
    """Validate image content and dimensions before running a detector."""
    try:
        with Image.open(path) as image:
            if image.width * image.height > max_pixels:
                raise ImageTooLargeError("Image exceeds the pixel limit.")
            image.load()
    except Image.DecompressionBombError as exc:
        raise ImageTooLargeError("Image exceeds the pixel limit.") from exc
    except ImageTooLargeError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImageError("Invalid or unsupported image.") from exc

    try:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise InvalidImageError("Invalid or unsupported image.") from exc
    if image is None:
        raise InvalidImageError("Invalid or unsupported image.")
