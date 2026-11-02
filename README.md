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
- [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/) for the HTTP API.

## HTTP API

Start the server from the repository root:

```bash
uv run uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Upload an image with:

```bash
curl -X POST "http://127.0.0.1:8000/detect" \
  -F "file=@checkbox_detection/data/image_dataset/image_1.png"
```

The default detector is `opencv_v2`. Select another registered detector with
the `detector` query parameter, for example `/detect?detector=opencv_v1`.
The response contains the detected checkboxes:

```json
{
  "boxes": [
    {"bbox": [10, 20, 30, 40], "is_checked": true}
  ]
}
```

Coordinates are inclusive `[x1, y1, x2, y2]` pixels; an image with no detected
checkboxes returns `{"boxes": []}`. Images must be readable by both Pillow
and OpenCV and are limited to 10 MiB per file and 25 million pixels. Invalid
images or unknown detectors return HTTP 400, oversized images return HTTP 413,
and detection failures return HTTP 500 without server file paths. A missing
file returns HTTP 422.

FastAPI's interactive documentation is available at `/docs`, alternative
documentation at `/redoc`, and the OpenAPI schema at `/openapi.json`. The
application checks uploaded file size after multipart parsing; when deploying
to untrusted clients, also configure a request-body limit at the ingress.

## Web interface

With the server running, open `http://127.0.0.1:8000/` to use the frontend: select
or drag and drop one or more PNG, JPG or JPEG images, run detection on the one
being shown, and inspect the results. Loaded images appear as thumbnails below
the viewer with their name and detection status; click one to show it or its ✕
to remove it. Checked boxes are outlined in green, unchecked boxes in red, and a
summary shows the total, checked and unchecked counts. The zoom controls keep
the image and its overlay aligned, and the image can be panned by clicking and
dragging. The frontend is plain HTML, CSS and
JavaScript in `frontend/`; it is served by the API itself, so no build step or
CORS configuration is needed, and all drawing happens in the browser.

## Dataset

Place the input images in:

```text
checkbox_detection/data/image_dataset/
```

The runner supports common image formats, including PNG, JPEG, BMP, GIF, TIFF, and WEBP.

## Running detection

Run the active detector with:

```bash
uv run python -m checkbox_detection.scripts.run_detection -d dummy_v1
```

The `dummy_v1` detector is a test detector that generates sample checkbox regions. It does not analyze the image contents.

To detect checkbox regions in the dataset with the `opencv_v1` detector, run:

```bash
uv run python -m checkbox_detection.scripts.run_detection -d opencv_v1
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
uv run python -m checkbox_detection.scripts.run_detection -d opencv_v2
```

Painted images are saved in:

```text
checkbox_detection/data/detection_results/<detector>/
```

The original images are preserved. Each result uses the original filename with `_painted` appended before the extension. For example:

```text
image_1.png -> checkbox_detection/data/detection_results/dummy_v1/image_1_painted.png
```

The output directory is cleared and recreated each time the detector runs.

## Evaluating a detector

Run a detector against every image in `checkbox_detection/data/image_dataset/` with:

```bash
uv run python -m checkbox_detection.scripts.run_detection_test -d dummy_v1
```

The evaluation report is saved to
`checkbox_detection/data/detection_results/<detector>_evaluation.json`. It includes per-image
matches, extra boxes, missed boxes, checked-state accuracy, and a summary.
The simple score is between 0 and 1:

```text
correctly matched states / max(expected boxes, detected boxes)
```

To paint the ground-truth annotations, run:

```bash
uv run python -m checkbox_detection.scripts.paint_ground_truth
```

## Project structure

```text
.
├── api/
│   ├── app.py                # FastAPI detection endpoint and static frontend
│   ├── schemas.py            # API response schema
│   └── tests/                # HTTP API tests
├── frontend/                 # Vanilla HTML/CSS/JS web interface
└── checkbox_detection/
    ├── detectors/            # Detector protocol, implementations, and registry
    ├── models.py             # Checkbox data model
    ├── evaluation.py         # Matching and evaluation metrics
    ├── painting.py           # Paints checkbox annotations on image copies
    ├── validation.py         # Image validation and domain errors
    ├── data/                 # Dataset, ground truth, and generated outputs
    ├── scripts/              # Detection, evaluation, and painting commands
    └── tests/                # Detection and workflow tests
```

The detection package is independent of FastAPI. Other Python code can import
`get_detector`, `available_detectors`, and `Checkbox` from `checkbox_detection`;
the API uses this public interface instead of the detector registry internals.
A frontend can also use the HTTP API without importing the Python package.

## Adding a detector

Implement the `CheckboxesDetector` protocol in `checkbox_detection/detectors/`,
then register the detector class in `checkbox_detection/detectors/factory.py`.
The registered name becomes available through the `-d` command-line option and
the API's `detector` query parameter.

## Running tests

```bash
uv run python -m unittest discover -s . -v
```
