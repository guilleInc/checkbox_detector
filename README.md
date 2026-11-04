# Checkbox Detector

Detects checkboxes in images (such as scanned forms). For each
checkbox it returns the bounding box (`[x1, y1, x2, y2]` in pixels) and whether
it is checked. It is exposed as a FastAPI service (`POST /detect`) with a small
web UI to upload an image and see the results.

## Try the hosted version!

The app is already deployed and can be tried without installing anything:

<https://checkbox-detector-2c01812c.fastapicloud.dev/>

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
