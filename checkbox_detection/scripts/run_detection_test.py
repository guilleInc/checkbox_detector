"""Evaluate a detector against the dataset ground truth.

Usage:
    uv run python -m checkbox_detection.scripts.run_detection_test -d dummy_v1

The JSON report is saved in checkbox_detection/data/detection_results/ by default.
The score is:

    correctly matched states / max(expected boxes, detected boxes)

This keeps the score between 0 and 1 while penalizing missed, extra, and
incorrectly classified checkboxes.
"""

import argparse
import json
from pathlib import Path

from checkbox_detection import available_detectors, get_detector
from checkbox_detection.evaluation import IOU_THRESHOLD, DetectionTestResult, run_detection_test
from checkbox_detection.scripts.paint_ground_truth import DEFAULT_GROUND_TRUTH_PATH, load_ground_truth

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "detection_results"


def simple_score(result: DetectionTestResult) -> float:
    """Return a simple score from 0 to 1 for a detection result."""
    denominator = max(result.expected_boxes, result.detected_boxes)
    if denominator == 0:
        return 0.0
    return result.matched_with_correct_state / denominator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a checkbox detector against the ground truth."
    )
    parser.add_argument(
        "-d",
        "--detector",
        required=True,
        choices=available_detectors(),
        help="name of the detector to evaluate",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GROUND_TRUTH_PATH,
        help=f"path to the ground-truth JSON (default: {DEFAULT_GROUND_TRUTH_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="path for the JSON report (default: checkbox_detection/data/detection_results/<detector>_evaluation.json)",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=IOU_THRESHOLD,
        help=f"IoU threshold for a match (default: {IOU_THRESHOLD})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotations = load_ground_truth(args.ground_truth)
    detector = get_detector(args.detector)
    aggregate = DetectionTestResult(image_name="all_images")
    image_results = []

    for image_path, expected in annotations:
        detected = detector.detect(image_path)
        result = run_detection_test(
            image_name=image_path.name,
            detected=detected,
            expected=expected,
            iou_threshold=args.iou_threshold,
        )
        aggregate.add(result)

        image_result = result.model_dump(mode="json")
        image_result["score"] = simple_score(result)
        image_results.append(image_result)
        print(
            f"{image_path.name}: score={image_result['score']:.3f}, "
            f"matched={result.matched_boxes}/{result.expected_boxes}, "
            f"extra={result.extra_boxes}, missed={result.missed_boxes}"
        )

    output_path = args.output or (
        DEFAULT_OUTPUT_DIR / f"{args.detector}_evaluation.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "detector": args.detector,
        "iou_threshold": args.iou_threshold,
        "score_definition": (
            "matched boxes with correct checked state / "
            "max(expected boxes, detected boxes)"
        ),
        "images": image_results,
        "summary": {
            **aggregate.model_dump(mode="json"),
            "score": simple_score(aggregate),
        },
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    main()
