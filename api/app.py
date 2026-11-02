import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from api.schemas import DetectionResponse
from checkbox_detection import (
    ImageTooLargeError,
    InvalidImageError,
    available_detectors,
    get_detector,
    validate_image,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
READ_CHUNK_BYTES = 1024 * 1024
FRONTEND_DIRECTORY = Path(__file__).resolve().parent.parent / "frontend"

logger = logging.getLogger(__name__)
app = FastAPI()


@app.post("/detect", response_model=DetectionResponse)
def detect(file: UploadFile = File(...), detector: str = "opencv_v2") -> DetectionResponse:
    if detector not in available_detectors():
        raise HTTPException(status_code=400, detail="Unknown detector.")

    try:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "upload"
            size = 0
            with path.open("wb") as output:
                while chunk := file.file.read(READ_CHUNK_BYTES):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="Upload exceeds the file size limit.")
                    output.write(chunk)
            validate_image(path, max_pixels=MAX_IMAGE_PIXELS)
            return DetectionResponse(boxes=get_detector(detector).detect(path))
    except ImageTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Image exceeds the pixel limit.") from exc
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Checkbox detection failed")
        raise HTTPException(status_code=500, detail="Checkbox detection failed.") from exc


# Mounted last so the API routes and the generated documentation take precedence.
app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
