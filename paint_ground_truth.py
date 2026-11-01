"""Paint the checkbox annotations from data/ground_truth.json onto the images.

Usage:
    uv run python paint_ground_truth.py

Annotated images are saved in data/ground_truth_results/ by default.
"""

import argparse
import json
import shutil
from pathlib import Path

from checkbox_painter import CheckboxPainter
from models import Checkbox

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_GROUND_TRUTH_PATH = BASE_DIR / "data" / "ground_truth.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "ground_truth_results"


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Paint ground-truth checkbox annotations onto dataset images."
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GROUND_TRUTH_PATH,
        help=f"path to the ground-truth JSON (default: {DEFAULT_GROUND_TRUTH_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"directory for painted images (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotations = load_ground_truth(args.ground_truth)

    if args.output_dir.exists() and not args.output_dir.is_dir():
        raise ValueError(f"Output path is not a directory: '{args.output_dir}'")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for existing_path in args.output_dir.iterdir():
        if existing_path.name == ".gitkeep":
            continue
        if existing_path.is_dir():
            shutil.rmtree(existing_path)
        else:
            existing_path.unlink()
    painter = CheckboxPainter(args.output_dir)

    for image_path, checkboxes in annotations:
        saved = painter.paint(image_path, checkboxes)
        print(f"{image_path.name}: {len(checkboxes)} checkboxes -> {saved}")


if __name__ == "__main__":
    main()
