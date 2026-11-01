from detectors.base_detector import CheckboxesDetector
from detectors.dummy_v1_detector import DummyV1CheckboxesDetector

DETECTORS = {
    "dummy_v1": DummyV1CheckboxesDetector,
}


def get_detector(name: str) -> CheckboxesDetector:
    """Return a new instance of the detector registered under `name`."""
    try:
        return DETECTORS[name]()
    except KeyError:
        available = ", ".join(sorted(DETECTORS))
        raise ValueError(f"Unknown detector '{name}'. Available: {available}") from None
