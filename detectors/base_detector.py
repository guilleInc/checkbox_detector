from pathlib import Path
from typing import Protocol

from models import Checkbox


class CheckboxesDetector(Protocol):
    def detect(self, image_path: Path) -> list[Checkbox]:
        """Return the checkboxes found in the image at `image_path`."""
        ...
