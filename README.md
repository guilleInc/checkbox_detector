# Checkbox Detector

Simple Python project for detecting checkboxes in images and painting the detected regions.

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/)

## Installation

Install the project dependencies with:

```bash
uv sync
```

The project currently uses:

- [Pillow](https://python-pillow.org/) for image loading and painting.
- [Pydantic](https://docs.pydantic.dev/) for checkbox data validation.

## Dataset

Place the input images in:

```text
data/image_dataset/
```

The runner supports common image formats, including PNG, JPEG, BMP, GIF, TIFF, and WEBP.

## Running detection

Run the active detector with:

```bash
uv run python run_detection.py -d dummy_v1
```

The `dummy_v1` detector is a test detector that generates sample checkbox regions. It does not analyze the image contents.

Painted images are saved in:

```text
data/detection_results/dummy_v1/
```

The original images are preserved. Each result uses the original filename with `_painted` appended before the extension. For example:

```text
image_1.png -> data/detection_results/dummy_v1/image_1_painted.png
```

The output directory is cleared and recreated each time the detector runs.

## Evaluating a detector

Run a detector against every image in `data/image_dataset/` with:

```bash
uv run python run_detection_test.py -d dummy_v1
```

The evaluation report is saved to
`data/detection_results/<detector>_evaluation.json`. It includes per-image
matches, extra boxes, missed boxes, checked-state accuracy, and a summary.
The simple score is between 0 and 1:

```text
correctly matched states / max(expected boxes, detected boxes)
```

## Project structure

```text
.
├── checkbox_painter.py       # Paints detected checkboxes on image copies
├── detectors/
│   ├── base_detector.py      # Detector protocol
│   ├── dummy_v1_detector.py  # Test detector
│   └── factory.py            # Detector registry
├── data/
│   ├── image_dataset/        # Input images
│   └── detection_results/    # Generated output images
├── models.py                 # Checkbox data model
├── run_detection.py          # Detector painting entry point
├── detection_test.py         # Matching and evaluation metrics
└── run_detection_test.py     # Evaluation command-line entry point
```

## Adding a detector

Implement the `CheckboxesDetector` protocol in `detectors/`, then register the detector class in `detectors/factory.py`. The registered name becomes available through the `-d` command-line option.
