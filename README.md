# Checkbox Detector

Simple Python project for detecting checkboxes in images and painting the detected regions.

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)

Alternatively, use [Docker](#running-with-docker) and skip installing Python and `uv`.

## Installation

Install the project dependencies with:

```bash
uv sync
```

The project currently uses:

- [Pillow](https://python-pillow.org/) for image loading and painting.
- [OpenCV](https://opencv.org/) for checkbox detection.
- [Pydantic](https://docs.pydantic.dev/) for checkbox data validation.
- [FastAPI](https://fastapi.tiangolo.com/) (`fastapi[standard]`, which includes the
  FastAPI CLI) and [Uvicorn](https://www.uvicorn.org/) for the HTTP API.

## Running with Docker

Start the web UI and API at `http://localhost:8000/`:

```bash
docker compose up --build
```

Run the CLI scripts and the test suite in the container:

```bash
docker compose run --rm api python -m checkbox_detection.scripts.run_detection -d opencv_v2
docker compose run --rm api python -m checkbox_detection.scripts.run_detection_test -d opencv_v2
docker compose run --rm api python -m unittest discover -s . -v
```

`checkbox_detection/data/` is mounted from the host, so images placed in
`image_dataset/` are picked up and results are written to the host's
`detection_results/`. The container runs as a non-root user with UID/GID 1000;
if your host user differs, build with
`HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose build` so the generated
files belong to you.

## Deploying to FastAPI Cloud

The app can be deployed to [FastAPI Cloud](https://fastapicloud.com/docs/) with
the FastAPI CLI, which is installed by `uv sync`. The Docker workflow is
unaffected.

```bash
uv sync
uv run fastapi login      # first time only; opens the browser
uv run fastapi deploy
```

The first `fastapi deploy` asks you to create or select an app; the choice is
stored in `.fastapicloud/` (git-ignored). Configuration used by the deploy:

- **Entrypoint**: `[tool.fastapi] entrypoint = "api.app:app"` in `pyproject.toml`,
  so `uv run fastapi dev` and `fastapi deploy` need no path argument.
- **Dependencies and Python**: installed from `pyproject.toml` and `uv.lock`;
  Python 3.14 comes from `requires-python` and `.python-version`.
  `opencv-python-headless` ships pre-built wheels, so no system packages are needed.
- **Bundle**: FastAPI Cloud uploads everything not matched by `.gitignore`, then
  applies `.fastapicloudignore`, which excludes tests, `checkbox_detection/data/`
  (dataset and ground truth), the CLI scripts and Docker files. `api/`,
  `checkbox_detection/` and `frontend/` are included; the frontend is plain
  static files, so there is no build step before deploying.

After deploying, check `/`, `/docs` and `POST /detect` on the app's URL, for example:

```bash
curl -X POST "https://<your-app>.fastapicloud.dev/detect" \
  -F "file=@checkbox_detection/data/image_dataset/image_1.png"
```

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

With the server running, open `http://127.0.0.1:8000/` to use the frontend. It
has three areas:

- **Upload Images**: select or drag and drop one or more PNG, JPG or JPEG images,
  or click **Try sample images** to load four bundled examples from
  `frontend/samples/` without uploading anything.
- **Loaded Images**: appears once at least one image is loaded. It lists
  thumbnails with each image's name and detection status; click one to show it
  in the viewer, or its ✕ to remove it.
- **Image Viewer**: shows the selected image, with its file name in the title. Detection runs
  on the image being shown. Checked boxes are outlined in green, unchecked boxes
  in red, and a summary shows the total, checked and unchecked counts. The zoom
  controls keep the image and its overlay aligned, and the image can be panned by
  clicking and dragging.

The frontend is plain HTML, CSS and JavaScript (ES modules) in `frontend/`; it is
served by the API itself, so no build step or CORS configuration is needed, and
all drawing happens in the browser. The Inter font is bundled in
`frontend/fonts/` under the SIL Open Font License.

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
├── frontend/                 # Vanilla HTML/CSS/JS web interface (samples/ holds the demo images)
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
