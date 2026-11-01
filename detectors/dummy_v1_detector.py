import random
from pathlib import Path

from PIL import Image

from models import Checkbox

BOX_SIZE = 25
CHECKED_COUNT = 10
UNCHECKED_COUNT = 4


class DummyV1CheckboxesDetector:
    """Test-only detector: returns random checkboxes without analyzing the image."""

    def detect(self, image_path: Path) -> list[Checkbox]:
        with Image.open(image_path) as image:
            width, height = image.size

        checkboxes = []
        for is_checked in [True] * CHECKED_COUNT + [False] * UNCHECKED_COUNT:
            x1 = random.randint(0, width - BOX_SIZE)
            y1 = random.randint(0, height - BOX_SIZE)
            checkboxes.append(
                Checkbox(
                    bbox=(x1, y1, x1 + BOX_SIZE - 1, y1 + BOX_SIZE - 1),
                    is_checked=is_checked,
                )
            )
        return checkboxes
