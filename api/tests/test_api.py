import asyncio
import io
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient
from PIL import Image

import api.app as api_app
import checkbox_detection.validation as validation
from checkbox_detection import Checkbox, get_detector


def image_bytes(size=(100, 100)):
    output = io.BytesIO()
    Image.new("1", size, 1).save(output, format="PNG")
    return output.getvalue()


class DetectionAPITest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        temporary_directory = tempfile.TemporaryDirectory
        temporary_patcher = patch.object(
            api_app.tempfile,
            "TemporaryDirectory",
            side_effect=lambda: temporary_directory(dir=self.root.name),
        )
        temporary_patcher.start()
        self.addCleanup(temporary_patcher.stop)
        self.client = TestClient(api_app.app)
        self.addCleanup(self.client.close)
        self.png = image_bytes()

    def tearDown(self):
        self.assertEqual(list(Path(self.root.name).iterdir()), [])

    def post_image(self, image=None, detector=None, filename="upload.png"):
        url = "/detect" if detector is None else f"/detect?detector={detector}"
        return self.client.post(
            url,
            files={"file": (filename, self.png if image is None else image, "image/png")},
        )

    def test_default_detector_and_response_shape(self):
        detector = Mock()
        detector.detect.return_value = [
            Checkbox(bbox=(10, 20, 30, 40), is_checked=True),
            Checkbox(bbox=(50, 60, 70, 80), is_checked=False),
        ]
        with patch.object(api_app, "get_detector", return_value=detector) as get:
            response = self.post_image(filename="../../untrusted.png")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"boxes": [
            {"bbox": [10, 20, 30, 40], "is_checked": True},
            {"bbox": [50, 60, 70, 80], "is_checked": False},
        ]})
        get.assert_called_once_with("opencv_v2")
        self.assertFalse(detector.detect.call_args.args[0].exists())

    def test_selected_detector_and_empty_result(self):
        detector = Mock()
        detector.detect.return_value = []
        with patch.object(api_app, "get_detector", return_value=detector) as get:
            response = self.post_image(detector="opencv_v1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"boxes": []})
        get.assert_called_once_with("opencv_v1")

    def test_real_detector_matches_existing_detector(self):
        image_path = (
            Path(__file__).resolve().parents[2]
            / "checkbox_detection/data/image_dataset/image_6.jpg"
        )
        expected = [box.model_dump(mode="json") for box in get_detector("opencv_v2").detect(image_path)]
        response = self.post_image(image_path.read_bytes(), filename=image_path.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"boxes": expected})

    def test_registered_dummy_detector(self):
        response = self.post_image(detector="dummy_v1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["boxes"]), 14)

    def test_missing_file_is_rejected(self):
        self.assertEqual(self.client.post("/detect").status_code, 422)

    def test_unknown_detector_is_rejected(self):
        with patch.object(api_app, "get_detector") as get:
            response = self.post_image(detector="unknown")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Unknown detector.")
        get.assert_not_called()

    def test_invalid_images_are_rejected(self):
        for data in (b"", b"not an image", self.png[:len(self.png) // 2]):
            with self.subTest(data=data[:20]):
                response = self.post_image(data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Invalid or unsupported image.")

    def test_image_unsupported_by_opencv_is_rejected(self):
        with patch.object(validation.cv2, "imread", return_value=None):
            response = self.post_image()
        self.assertEqual(response.status_code, 400)

    def test_decompression_bomb_is_rejected_as_oversized(self):
        with patch.object(validation.Image, "open", side_effect=Image.DecompressionBombError):
            response = self.post_image()
        self.assertEqual(response.status_code, 413)

    def test_content_not_filename_or_mime_type_is_validated(self):
        detector = Mock()
        detector.detect.return_value = []
        with patch.object(api_app, "get_detector", return_value=detector):
            response = self.client.post(
                "/detect",
                files={"file": ("file.txt", self.png, "text/plain")},
            )
        self.assertEqual(response.status_code, 200)

    def test_upload_file_size_limit_is_inclusive(self):
        at_limit = self.png + b"\0" * (api_app.MAX_UPLOAD_BYTES - len(self.png))
        detector = Mock()
        detector.detect.return_value = []
        with patch.object(api_app, "get_detector", return_value=detector):
            self.assertEqual(self.post_image(at_limit).status_code, 200)
            self.assertEqual(self.post_image(at_limit + b"\0").status_code, 413)

    def test_pixel_limit_is_inclusive(self):
        detector = Mock()
        detector.detect.return_value = []
        with patch.object(api_app, "get_detector", return_value=detector):
            self.assertEqual(self.post_image(image_bytes((5000, 5000))).status_code, 200)
            self.assertEqual(self.post_image(image_bytes((5001, 5000))).status_code, 413)

    def test_detector_failure_is_logged_and_sanitized(self):
        detector = Mock()
        detector.detect.side_effect = ValueError("private path /tmp/secret/upload")
        with patch.object(api_app, "get_detector", return_value=detector):
            with self.assertLogs("api.app", level="ERROR"):
                response = self.post_image()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Checkbox detection failed."})
        self.assertFalse(detector.detect.call_args.args[0].exists())

    def test_default_documentation_routes_are_available(self):
        for path in ("/docs", "/redoc", "/openapi.json"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/detect", schema["paths"])
        self.assertEqual(
            set(schema["components"]["schemas"]["DetectionResponse"]["properties"]),
            {"boxes"},
        )

    def test_frontend_is_served_without_shadowing_api_routes(self):
        index = self.client.get("/")
        self.assertEqual(index.status_code, 200)
        self.assertIn("text/html", index.headers["content-type"])
        self.assertIn("Checkbox Detector", index.text)
        for path in ("/app.js", "/styles.css"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get("/missing.js").status_code, 404)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.client.post("/detect").status_code, 422)

    def test_detection_does_not_run_on_event_loop_thread(self):
        detector = Mock()
        detector.detect.return_value = []

        async def make_request():
            event_loop_thread = threading.get_ident()
            detector.detect.side_effect = lambda _: self.assertNotEqual(
                threading.get_ident(), event_loop_thread
            ) or []
            transport = httpx.ASGITransport(app=api_app.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/detect", files={"file": ("image.png", self.png, "image/png")}
                )
            self.assertEqual(response.status_code, 200)

        with patch.object(api_app, "get_detector", return_value=detector):
            asyncio.run(make_request())

    def test_concurrent_requests_use_distinct_temporary_files(self):
        barrier = threading.Barrier(2, timeout=10)
        paths = []
        detector = Mock()

        def detect(path):
            paths.append(path)
            barrier.wait()
            self.assertTrue(path.is_file())
            return []

        detector.detect.side_effect = detect

        async def make_requests():
            transport = httpx.ASGITransport(app=api_app.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                responses = await asyncio.gather(*[
                    client.post("/detect", files={"file": ("image.png", self.png, "image/png")})
                    for _ in range(2)
                ])
            self.assertEqual([response.status_code for response in responses], [200, 200])

        with patch.object(api_app, "get_detector", return_value=detector):
            asyncio.run(make_requests())
        self.assertEqual(len(set(paths)), 2)
        self.assertTrue(all(not path.exists() for path in paths))


if __name__ == "__main__":
    unittest.main()
