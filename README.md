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
- [OpenCV](https://opencv.org/) for checkbox detection.
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

To detect checkbox regions in the dataset with the `opencv_v1` detector, run:

```bash
uv run python run_detection.py -d opencv_v1
```

The `opencv_v1` detector uses OpenCV to find square checkbox contours and
classifies a box as checked when its interior contains a substantial dark
mark. It returns both checked and unchecked boxes.

The `opencv_v2` detector is fully self-contained (it does not import any other
detector). It combines multi-threshold contours, duplicate suppression, and
conservative image-local scale filtering. If at least 5 adaptive-threshold
candidates fall outside the standard checkbox size band, it switches to its
adaptive strategy (adaptive thresholding, wider size range and border
validation):

```bash
uv run python run_detection.py -d opencv_v2
```

Painted images are saved in:

```text
data/detection_results/<detector>/
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
│   ├── opencv_v1_detector.py # OpenCV v1 checkbox detector
│   ├── opencv_v2_detector.py # OpenCV v2 self-contained detector
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
