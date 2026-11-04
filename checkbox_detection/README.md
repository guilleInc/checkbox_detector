# checkbox_detection

## Testing environment

This module provides a testing environment that makes it easy to develop, run,
and compare different checkbox detectors.

- **`CheckboxesDetector` interface:** defines the input and output expected
  from each detector implementation, so all solutions follow a common structure.
- **Image dataset:** the images provided as part of the challenge, used as the
  basis for testing the implementations.
- **Painter:** takes the coordinates and state of the detected checkboxes and
  draws them over the images to make visual inspection easy.
- **Execution scripts:** select a detector, run it against the dataset images,
  and save the annotated images and an evaluation report.

The goal is a common structure for testing different tools and strategies
independently, making it easier to compare results and collaborate as a team.

## Structure

```
checkbox_detection/
├── detectors/
│   ├── base_detector.py       # CheckboxesDetector interface
│   ├── detector_factory.py    # detector registry (name -> class)
│   └── *_detector.py          # implementations (dummy_v1, opencv_v1, opencv_v2)
├── scripts/
│   ├── run_detection.py       # run a detector over the dataset and paint results
│   └── run_detector_evaluation.py  # score a detector against the ground truth
├── data/
│   ├── image_dataset/         # input images
│   ├── ground_truth.json      # expected checkboxes per image
│   └── detection_results/     # generated output (git-ignored)
├── checkboxes_painter.py      # draws checkboxes over images
├── detector_evaluator.py      # matches detections to ground truth (IoU) and scores them
├── ground_truth.py            # loads ground_truth.json
├── models.py                  # Checkbox model (bbox + is_checked)
├── validation.py              # image validation
└── tests/
```

## Usage

Run from the repository root. `-d` takes a detector name from
`detector_factory.py` (`dummy_v1`, `opencv_v1`, `opencv_v2`).

Run a detector over the dataset and save the painted images to
`data/detection_results/<detector>/`:

```bash
uv run python -m checkbox_detection.scripts.run_detection -d opencv_v2
```

Evaluate a detector against `ground_truth.json` and save a JSON report to
`data/detection_results/<detector>_evaluation.json`:

```bash
uv run python -m checkbox_detection.scripts.run_detector_evaluation -d opencv_v2
```

Run the tests:

```bash
uv run python -m unittest discover -s . -v
```

## Adding a detector

1. Create `detectors/<name>_detector.py` with a class implementing
   `detect(image_path) -> list[Checkbox]`.
2. Register it in `DETECTORS` in `detectors/detector_factory.py`.
