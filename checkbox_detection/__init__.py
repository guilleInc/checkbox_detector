"""Public interface for checkbox detection."""

from checkbox_detection.detectors.factory import available_detectors, get_detector
from checkbox_detection.models import Checkbox
from checkbox_detection.validation import ImageTooLargeError, InvalidImageError, validate_image

__all__ = [
    "Checkbox",
    "ImageTooLargeError",
    "InvalidImageError",
    "available_detectors",
    "get_detector",
    "validate_image",
]
