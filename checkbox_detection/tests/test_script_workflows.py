import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from checkbox_detection.scripts import run_detection


class ScriptWorkflowTest(unittest.TestCase):
    def test_detection_and_evaluation_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_dir = root / "images"
            image_dir.mkdir()
            image_path = image_dir / "sample.png"
            Image.new("RGB", (100, 100), "white").save(image_path)
            ground_truth = root / "ground_truth.json"
            ground_truth.write_text(json.dumps({
                "images": [{"image": str(image_path), "boxes": []}]
            }), encoding="utf-8")

            results = root / "results"
            with patch.object(run_detection, "IMAGE_DATASET_DIR", image_dir), \
                 patch.object(run_detection, "DETECTION_RESULTS_DIR", results), \
                 patch.object(sys, "argv", ["run_detection", "-d", "dummy_v1"]):
                run_detection.main()
            self.assertTrue((results / "dummy_v1" / "sample_painted.png").is_file())

            report = root / "evaluation.json"
            subprocess.run(
                [sys.executable, "-m", "checkbox_detection.scripts.run_detector_evaluation", "-d", "dummy_v1",
                 "--ground-truth", str(ground_truth), "--output", str(report)],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(json.loads(report.read_text())["summary"]["detected_boxes"], 14)


if __name__ == "__main__":
    unittest.main()
