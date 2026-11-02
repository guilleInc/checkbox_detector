from pydantic import BaseModel, Field

from checkbox_detection.models import Checkbox

IOU_THRESHOLD = 0.5


class DetectionTestResult(BaseModel):
    """Detection metrics and the boxes that were missed or added by a detector."""

    image_name: str = ""
    expected_boxes: int = 0
    expected_checked: int = 0
    expected_unchecked: int = 0
    detected_boxes: int = 0
    matched_boxes: int = 0
    extra_boxes: int = 0
    missed_boxes: int = 0
    matched_with_correct_state: int = 0
    extra_box_details: list[Checkbox] = Field(default_factory=list)
    missed_box_details: list[Checkbox] = Field(default_factory=list)

    def add(self, other: "DetectionTestResult") -> None:
        """Accumulate another result, including its unmatched boxes."""
        self.expected_boxes += other.expected_boxes
        self.expected_checked += other.expected_checked
        self.expected_unchecked += other.expected_unchecked
        self.detected_boxes += other.detected_boxes
        self.matched_boxes += other.matched_boxes
        self.extra_boxes += other.extra_boxes
        self.missed_boxes += other.missed_boxes
        self.matched_with_correct_state += other.matched_with_correct_state
        self.extra_box_details.extend(other.extra_box_details)
        self.missed_box_details.extend(other.missed_box_details)


def box_area(box: Checkbox) -> int:
    x1, y1, x2, y2 = box.bbox
    return (x2 - x1 + 1) * (y2 - y1 + 1)


def iou(box_a: Checkbox, box_b: Checkbox) -> float:
    """Return intersection over union for inclusive pixel coordinates."""
    overlap_width = (
        min(box_a.bbox[2], box_b.bbox[2])
        - max(box_a.bbox[0], box_b.bbox[0])
        + 1
    )
    overlap_height = (
        min(box_a.bbox[3], box_b.bbox[3])
        - max(box_a.bbox[1], box_b.bbox[1])
        + 1
    )
    if overlap_width <= 0 or overlap_height <= 0:
        return 0.0

    intersection = overlap_width * overlap_height
    union = box_area(box_a) + box_area(box_b) - intersection
    return intersection / union


def _match_boxes(
    detected: list[Checkbox],
    expected: list[Checkbox],
    iou_threshold: float,
) -> list[tuple[int, int]]:
    """Match as many boxes as possible with IoU above the threshold."""
    candidates: list[list[tuple[float, int]]] = []
    for expected_box in expected:
        expected_candidates = []
        for detected_index, detected_index_box in enumerate(detected):
            overlap = iou(detected_index_box, expected_box)
            if overlap >= iou_threshold:
                expected_candidates.append((overlap, detected_index))
        expected_candidates.sort(
            key=lambda pair: (-pair[0], pair[1]),
        )
        candidates.append(expected_candidates)

    assigned_expected_by_detected: dict[int, int] = {}

    def assign(expected_index: int, visited_detected: set[int]) -> bool:
        for _, detected_index in candidates[expected_index]:
            if detected_index in visited_detected:
                continue

            visited_detected.add(detected_index)
            previous_expected_index = assigned_expected_by_detected.get(detected_index)
            if (
                previous_expected_index is None
                or assign(previous_expected_index, visited_detected)
            ):
                assigned_expected_by_detected[detected_index] = expected_index
                return True

        return False

    expected_order = sorted(
        range(len(expected)),
        key=lambda expected_index: len(candidates[expected_index]),
    )
    for expected_index in expected_order:
        assign(expected_index, set())

    return sorted(
        (
            detected_index,
            expected_index,
        )
        for detected_index, expected_index in assigned_expected_by_detected.items()
    )


def run_detection_test(
    image_name: str,
    detected: list[Checkbox],
    expected: list[Checkbox],
    iou_threshold: float = IOU_THRESHOLD,
) -> DetectionTestResult:
    """Compare detected boxes with expected boxes and retain unmatched details."""
    if not 0.0 <= iou_threshold <= 1.0:
        raise ValueError("iou_threshold must be between 0 and 1")

    matches = _match_boxes(detected, expected, iou_threshold)
    matched_detected_indices = {detected_index for detected_index, _ in matches}
    matched_expected_indices = {expected_index for _, expected_index in matches}

    extra_box_details = [
        box
        for index, box in enumerate(detected)
        if index not in matched_detected_indices
    ]
    missed_box_details = [
        box
        for index, box in enumerate(expected)
        if index not in matched_expected_indices
    ]
    matched_with_correct_state = sum(
        detected[detected_index].is_checked
        == expected[expected_index].is_checked
        for detected_index, expected_index in matches
    )
    expected_checked = sum(box.is_checked for box in expected)

    return DetectionTestResult(
        image_name=image_name,
        expected_boxes=len(expected),
        expected_checked=expected_checked,
        expected_unchecked=len(expected) - expected_checked,
        detected_boxes=len(detected),
        matched_boxes=len(matches),
        extra_boxes=len(extra_box_details),
        missed_boxes=len(missed_box_details),
        matched_with_correct_state=matched_with_correct_state,
        extra_box_details=extra_box_details,
        missed_box_details=missed_box_details,
    )
