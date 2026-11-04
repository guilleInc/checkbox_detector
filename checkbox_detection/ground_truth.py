import json
from pathlib import Path

from checkbox_detection.models import Checkbox

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_GROUND_TRUTH_PATH = BASE_DIR / "data" / "ground_truth.json"


def load_ground_truth(path: Path) -> list[tuple[Path, list[Checkbox]]]:
    """Load and validate image paths and checkbox annotations from JSON."""
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read ground truth file '{path}': {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("images"), list):
        raise ValueError(f"'{path}' must contain an 'images' list")

    annotations = []
    for index, entry in enumerate(data["images"], start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Ground-truth entry {index} must be an object")

        image_value = entry.get("image")
        boxes_value = entry.get("boxes")
        if not isinstance(image_value, str) or not isinstance(boxes_value, list):
            raise ValueError(
                f"Ground-truth entry {index} must contain an image string and boxes list"
            )

        image_path = Path(image_value)
        if not image_path.is_absolute():
            image_path = BASE_DIR / image_path
        if not image_path.is_file():
            raise ValueError(
                f"Ground-truth entry {index} references missing image '{image_value}'"
            )

        try:
            checkboxes = [Checkbox.model_validate(box) for box in boxes_value]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid boxes in ground-truth entry {index}: {exc}") from exc

        annotations.append((image_path, checkboxes))

    return annotations
