from checkbox_detection.detectors.base_detector import CheckboxesDetector
from checkbox_detection.detectors.dummy_v1_detector import DummyV1CheckboxesDetector
from checkbox_detection.detectors.opencv_v1_detector import OpenCVV1CheckboxesDetector
from checkbox_detection.detectors.opencv_v2_detector import OpenCVV2CheckboxesDetector

DETECTORS = {
    "dummy_v1": DummyV1CheckboxesDetector,
    "opencv_v1": OpenCVV1CheckboxesDetector,
    "opencv_v2": OpenCVV2CheckboxesDetector,
}


def available_detectors() -> tuple[str, ...]:
    """Return registered detector names in a stable order."""
    return tuple(sorted(DETECTORS))


def get_detector(name: str) -> CheckboxesDetector:
    """Return a new instance of the detector registered under `name`."""
    try:
        return DETECTORS[name]()
    except KeyError:
        available = ", ".join(available_detectors())
        raise ValueError(f"Unknown detector '{name}'. Available: {available}") from None
