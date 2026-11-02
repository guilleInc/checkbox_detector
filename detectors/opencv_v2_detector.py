"""Self-contained OpenCV checkbox detector.

Two strategies share one entry point:

* adaptive: adaptive thresholding with border validation and a wide size band,
  used when the page contains checkboxes outside the standard size band.
* standard: multi-threshold contours, duplicate suppression and image-local
  scale filtering, tuned for checkboxes of a typical size.
"""

from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from models import Checkbox

Rect = tuple[int, int, int, int]  # x, y, width, height

# Standard strategy: candidate side length as a fraction of the image width.
STANDARD_MIN_SIDE_FRAC = 0.0075
STANDARD_MAX_SIDE_FRAC = 0.02
STANDARD_MIN_ASPECT = 0.65
STANDARD_MAX_ASPECT = 1.4
STANDARD_MIN_RECTANGULARITY = 0.75
STANDARD_THRESHOLDS = (155, 165, 175, 185)
DUPLICATE_IOU_THRESHOLD = 0.5
CHECKED_INK_THRESHOLD = 160
CHECKED_MIN_INK_RATIO = 0.08
MIN_BOXES_FOR_SCALE_FILTER = 5
MIN_SCALE_RATIO = 0.8
MAX_SCALE_RATIO = 1.2

# Adaptive strategy.
ADAPTIVE_MIN_SIDE_FRAC = 0.006
ADAPTIVE_MAX_SIDE_FRAC = 0.03
ADAPTIVE_MAX_ASPECT_DEVIATION = 0.3
ADAPTIVE_MIN_RECTANGULARITY = 0.8
ADAPTIVE_BORDER_STRIP_FRAC = 0.1
ADAPTIVE_MIN_BORDER_COVERAGE = 0.9
ADAPTIVE_INTERIOR_MARGIN_FRAC = 0.2
ADAPTIVE_CHECKED_FILL_RATIO = 0.08
ADAPTIVE_CHECKED_MIN_COMPONENT_FRAC = 0.04

# Use the adaptive strategy when this many adaptive candidates fall outside
# the standard size band.
MIN_OUT_OF_BAND_BOXES = 5


class OpenCVV2CheckboxesDetector:
    """Detect checkboxes and infer whether their interiors are marked."""

    def detect(self, image_path: Path) -> list[Checkbox]:
        image_path = Path(image_path)
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unable to read image '{image_path}'")

        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        adaptive_boxes = self._detect_adaptive(grayscale)
        if self._has_out_of_band_boxes(grayscale.shape[1], adaptive_boxes):
            return adaptive_boxes
        return self._detect_standard(grayscale)

    # Standard strategy

    def _detect_standard(self, grayscale: np.ndarray) -> list[Checkbox]:
        candidates = self._standard_candidates(grayscale)
        return self._filter_by_dominant_scale(self._deduplicate(candidates))

    def _standard_candidates(self, grayscale: np.ndarray) -> list[Checkbox]:
        image_width = grayscale.shape[1]
        min_side = round(image_width * STANDARD_MIN_SIDE_FRAC)
        max_side = round(image_width * STANDARD_MAX_SIDE_FRAC)
        candidates = []

        for threshold in STANDARD_THRESHOLDS:
            binary = cv2.threshold(
                grayscale, threshold, 255, cv2.THRESH_BINARY_INV
            )[1]
            contours, _ = cv2.findContours(
                binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                rect = self._standard_rect(
                    contour, min_side=min_side, max_side=max_side
                )
                if rect is None:
                    continue
                x, y, width, height = rect
                candidates.append(
                    Checkbox(
                        bbox=(x, y, x + width - 1, y + height - 1),
                        is_checked=self._is_checked_by_ink(grayscale, rect),
                    )
                )
        return candidates

    @staticmethod
    def _standard_rect(contour, *, min_side: int, max_side: int) -> Rect | None:
        x, y, width, height = cv2.boundingRect(contour)
        if not (min_side <= width <= max_side and min_side <= height <= max_side):
            return None
        if not STANDARD_MIN_ASPECT <= width / height <= STANDARD_MAX_ASPECT:
            return None
        if cv2.contourArea(contour) / (width * height) < STANDARD_MIN_RECTANGULARITY:
            return None

        perimeter = cv2.arcLength(contour, True)
        vertices = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if not 4 <= len(vertices) <= 8:
            return None
        return x, y, width, height

    @staticmethod
    def _is_checked_by_ink(grayscale: np.ndarray, rect: Rect) -> bool:
        x, y, width, height = rect
        margin_x = max(2, width // 4)
        margin_y = max(2, height // 4)
        interior = grayscale[
            y + margin_y : y + height - margin_y,
            x + margin_x : x + width - margin_x,
        ]
        if interior.size == 0:
            return False
        return bool((interior < CHECKED_INK_THRESHOLD).mean() >= CHECKED_MIN_INK_RATIO)

    @classmethod
    def _deduplicate(cls, candidates: list[Checkbox]) -> list[Checkbox]:
        """Keep the largest candidate from each group of overlapping boxes."""
        selected: list[Checkbox] = []
        for candidate in sorted(
            candidates,
            key=lambda box: (-cls._area(box), *reversed(box.bbox[:2]), *box.bbox[2:]),
        ):
            if any(
                cls._iou(candidate, kept) >= DUPLICATE_IOU_THRESHOLD
                for kept in selected
            ):
                continue
            selected.append(candidate)
        return sorted(selected, key=lambda box: (box.bbox[1], box.bbox[0]))

    @staticmethod
    def _size(box: Checkbox) -> tuple[int, int]:
        x1, y1, x2, y2 = box.bbox
        return x2 - x1 + 1, y2 - y1 + 1

    @classmethod
    def _area(cls, box: Checkbox) -> int:
        width, height = cls._size(box)
        return width * height

    @classmethod
    def _iou(cls, box_a: Checkbox, box_b: Checkbox) -> float:
        x1 = max(box_a.bbox[0], box_b.bbox[0])
        y1 = max(box_a.bbox[1], box_b.bbox[1])
        x2 = min(box_a.bbox[2], box_b.bbox[2])
        y2 = min(box_a.bbox[3], box_b.bbox[3])
        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1 + 1) * (y2 - y1 + 1)
        union = cls._area(box_a) + cls._area(box_b) - intersection
        return intersection / union

    @classmethod
    def _filter_by_dominant_scale(cls, boxes: list[Checkbox]) -> list[Checkbox]:
        if len(boxes) < MIN_BOXES_FOR_SCALE_FILTER:
            return boxes

        dominant_width, dominant_height = Counter(
            cls._size(box) for box in boxes
        ).most_common(1)[0][0]
        return [
            box
            for box in boxes
            if MIN_SCALE_RATIO <= cls._size(box)[0] / dominant_width <= MAX_SCALE_RATIO
            and MIN_SCALE_RATIO <= cls._size(box)[1] / dominant_height <= MAX_SCALE_RATIO
        ]

    # Adaptive strategy

    def _detect_adaptive(self, grayscale: np.ndarray) -> list[Checkbox]:
        binary = cv2.adaptiveThreshold(
            grayscale,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            10,
        )
        rects = [
            rect
            for rect in self._adaptive_candidates(binary)
            if self._has_straight_border(binary, rect)
        ]

        boxes = []
        for rect in self._dedupe_by_center(rects):
            x, y, width, height = rect
            boxes.append(
                Checkbox(
                    bbox=(x, y, x + width - 1, y + height - 1),
                    is_checked=self._is_checked_by_component(binary, rect),
                )
            )
        return sorted(boxes, key=lambda box: (box.bbox[1], box.bbox[0]))

    @staticmethod
    def _adaptive_candidates(binary: np.ndarray) -> list[Rect]:
        image_width = binary.shape[1]
        min_side = ADAPTIVE_MIN_SIDE_FRAC * image_width
        max_side = ADAPTIVE_MAX_SIDE_FRAC * image_width
        contours, _ = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        rects = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            if not (min_side <= width <= max_side and min_side <= height <= max_side):
                continue
            if abs(width / height - 1) > ADAPTIVE_MAX_ASPECT_DEVIATION:
                continue

            perimeter = cv2.arcLength(contour, True)
            if len(cv2.approxPolyDP(contour, 0.05 * perimeter, True)) != 4:
                continue
            if cv2.contourArea(contour) / (width * height) < ADAPTIVE_MIN_RECTANGULARITY:
                continue
            rects.append((x, y, width, height))
        return rects

    @staticmethod
    def _has_straight_border(binary: np.ndarray, rect: Rect) -> bool:
        """Return whether all four sides are nearly continuous lines of ink."""
        x, y, width, height = rect
        t = max(2, int(min(width, height) * ADAPTIVE_BORDER_STRIP_FRAC))
        padded = cv2.copyMakeBorder(binary, t, t, t, t, cv2.BORDER_CONSTANT, value=0)
        x, y = x + t, y + t
        strips = [
            padded[y - t : y + t, x : x + width].any(axis=0),
            padded[y + height - t : y + height + t, x : x + width].any(axis=0),
            padded[y : y + height, x - t : x + t].any(axis=1),
            padded[y : y + height, x + width - t : x + width + t].any(axis=1),
        ]
        return all(strip.mean() >= ADAPTIVE_MIN_BORDER_COVERAGE for strip in strips)

    @staticmethod
    def _dedupe_by_center(rects: list[Rect]) -> list[Rect]:
        """Drop a rectangle whose center lies inside a larger kept rectangle."""
        kept: list[Rect] = []
        for x, y, width, height in sorted(
            rects, key=lambda rect: rect[2] * rect[3], reverse=True
        ):
            center_x, center_y = x + width / 2, y + height / 2
            if any(
                kx <= center_x <= kx + kw and ky <= center_y <= ky + kh
                for kx, ky, kw, kh in kept
            ):
                continue
            kept.append((x, y, width, height))
        return kept

    @staticmethod
    def _is_checked_by_component(binary: np.ndarray, rect: Rect) -> bool:
        """Checked when the border-excluded interior holds one sizeable ink blob."""
        x, y, width, height = rect
        margin_x = int(width * ADAPTIVE_INTERIOR_MARGIN_FRAC)
        margin_y = int(height * ADAPTIVE_INTERIOR_MARGIN_FRAC)
        interior = binary[
            y + margin_y : y + height - margin_y,
            x + margin_x : x + width - margin_x,
        ]
        if interior.size == 0:
            return False

        fill_ratio = np.count_nonzero(interior) / interior.size
        component_count, _, stats, _ = cv2.connectedComponentsWithStats(
            interior, connectivity=8
        )
        largest = stats[1:, cv2.CC_STAT_AREA].max() if component_count > 1 else 0
        return bool(
            fill_ratio >= ADAPTIVE_CHECKED_FILL_RATIO
            and largest / interior.size >= ADAPTIVE_CHECKED_MIN_COMPONENT_FRAC
        )

    # Strategy selection

    @classmethod
    def _has_out_of_band_boxes(
        cls, image_width: int, boxes: list[Checkbox]
    ) -> bool:
        min_side = round(image_width * STANDARD_MIN_SIDE_FRAC)
        max_side = round(image_width * STANDARD_MAX_SIDE_FRAC)
        out_of_band = sum(
            not (min_side <= width <= max_side and min_side <= height <= max_side)
            for width, height in map(cls._size, boxes)
        )
        return out_of_band >= MIN_OUT_OF_BAND_BOXES
