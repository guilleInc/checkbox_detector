# Checkbox Detector

Detects checkboxes in images (such as scanned forms). For each
checkbox it returns the bounding box (`[x1, y1, x2, y2]` in pixels) and whether
it is checked. It is exposed as a FastAPI service (`POST /detect`) with a small
web UI to upload an image and see the results.

## Try the hosted version!

The app is already deployed and can be tried without installing anything:

<https://checkbox-detector-2c01812c.fastapicloud.dev/>

## Accepted images

- **Format:** PNG or JPEG (`.png`, `.jpg`, `.jpeg`). The web UI only accepts
  these. The API validates the file content, not its name or MIME type, so
  other formats the server can decode may also work, but only PNG and JPEG are
  supported.
- **File size:** up to 10 MiB.
- **Resolution:** up to 25 megapixels (width × height, e.g. 5000 × 5000). An A4
  page scanned at 300 DPI is about 8.7 megapixels.

`POST /detect` answers `400` for an unreadable or unsupported image and `413`
when the file size or the resolution exceeds the limits.

## Running locally with Docker

The app is served at `http://localhost:8000/`. Before starting, make sure no
other service is listening on port 8000:

```bash
ss -ltnp | grep ':8000'   # no output = port is free
```

Start it:

```bash
sudo docker compose up
```

On the first run Docker builds the image automatically. To stop it, press
`Ctrl+C`, or from another terminal run:

```bash
sudo docker compose down
```

## Testing only the endpoint

FastAPI's built-in interactive docs let you call the detection endpoint
without the web UI. Open `/docs` on the hosted app
(<https://checkbox-detector-2c01812c.fastapicloud.dev/docs>) or on a local run
(`http://localhost:8000/docs`), then:

1. Expand `POST /detect`.
2. Click **Try it out**.
3. Choose the image file to upload (optionally set `detector`; the default is
   `opencv_v2`).
4. Click **Execute** and read the detections in the response body.

## Development setup

Requirements:

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)

Install the dependencies (creates `.venv/`):

```bash
uv sync
```

Run the API with auto-reload (web UI at `http://127.0.0.1:8000/`):

```bash
uv run fastapi dev
```

Run the tests:

```bash
uv run python -m unittest discover -s . -v
```

For the detection scripts and the module layout, see
[`checkbox_detection/README.md`](checkbox_detection/README.md).
