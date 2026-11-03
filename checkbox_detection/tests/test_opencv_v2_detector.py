import unittest
from pathlib import Path

from checkbox_detection.detectors.factory import get_detector
from checkbox_detection.detectors.opencv_v2_detector import OpenCVV2CheckboxesDetector
from checkbox_detection.evaluation import run_detection_test
from checkbox_detection.models import Checkbox
from checkbox_detection.scripts.paint_ground_truth import load_ground_truth


BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "data" / "image_dataset"


class OpenCVV2DetectorTest(unittest.TestCase):
    def setUp(self):
        self.detector = get_detector("opencv_v2")

    def test_detector_is_registered(self):
        self.assertEqual(
            type(self.detector).__name__,
            "OpenCVV2CheckboxesDetector",
        )

    def test_annotated_images_keep_accuracy_without_state_regression(self):
        results = {}
        for image_path, expected in load_ground_truth(
            BASE_DIR / "data" / "ground_truth.json"
        ):
            result = run_detection_test(
                image_path.name,
                self.detector.detect(image_path),
                expected,
            )
            results[image_path.name] = result
            self.assertEqual(result.matched_boxes, result.matched_with_correct_state)

        self.assertEqual(results["image_7.png"].extra_boxes, 0)
        self.assertLessEqual(sum(r.extra_boxes for r in results.values()), 1)
        self.assertGreaterEqual(sum(r.matched_boxes for r in results.values()), 277)

    def test_large_checkbox_images_are_detected(self):
        for image_name, minimum in (("image_1.png", 100), ("image_3.png", 40)):
            image_path = IMAGE_DIR / image_name
            if not image_path.exists():
                self.skipTest(f"{image_name} is not available")
            self.assertGreaterEqual(len(self.detector.detect(image_path)), minimum)

    def test_few_out_of_band_boxes_do_not_select_the_adaptive_strategy(self):
        stray = Checkbox(bbox=(0, 0, 99, 99), is_checked=False)

        self.assertFalse(
            OpenCVV2CheckboxesDetector._has_out_of_band_boxes(1700, [stray])
        )
        self.assertTrue(
            OpenCVV2CheckboxesDetector._has_out_of_band_boxes(1700, [stray] * 5)
        )

    def test_dominant_scale_filter_drops_outlier_sizes(self):
        regular = [
            Checkbox(bbox=(i * 40, 0, i * 40 + 24, 24), is_checked=False)
            for i in range(5)
        ]
        outlier = Checkbox(bbox=(0, 100, 9, 109), is_checked=False)

        kept = OpenCVV2CheckboxesDetector._filter_by_dominant_scale(
            regular + [outlier]
        )

        self.assertEqual(kept, regular)


if __name__ == "__main__":
    unittest.main()
