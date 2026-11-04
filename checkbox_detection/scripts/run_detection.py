"""Run a checkbox detector over every image in checkbox_detection/data/image_dataset/.

Usage:
    python -m checkbox_detection.scripts.run_detection -d dummy_v1

Painted images are saved in checkbox_detection/data/detection_results/<detector>/.
If that folder already exists, it is emptied first.
"""

import argparse
import shutil
import sys
from pathlib import Path

from checkbox_detection import available_detectors, get_detector
from checkbox_detection.checkboxes_painter import CheckboxPainter

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DATASET_DIR = BASE_DIR / "data" / "image_dataset"
DETECTION_RESULTS_DIR = BASE_DIR / "data" / "detection_results"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect checkboxes in checkbox_detection/data/image_dataset/ and paint the results."
    )
    parser.add_argument(
        "-d",
        dest="detector",
        required=True,
        choices=available_detectors(),
        help="name of the detector to use",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    detector = get_detector(args.detector)

    image_paths = sorted(
        p for p in IMAGE_DATASET_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        sys.exit(f"No images found in '{IMAGE_DATASET_DIR}'.")

    output_dir = DETECTION_RESULTS_DIR / args.detector
    if output_dir.exists():
        shutil.rmtree(output_dir)
    painter = CheckboxPainter(output_dir)

    for image_path in image_paths:
        try:
            checkboxes = detector.detect(image_path)
            saved = painter.paint(image_path, checkboxes)
        except (OSError, ValueError) as exc:
            print(f"Skipped {image_path.name}: {exc}")
            continue
        print(f"{image_path.name}: {len(checkboxes)} checkboxes -> {saved}")


if __name__ == "__main__":
    main()
