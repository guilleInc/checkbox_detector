from pathlib import Path

import cv2

from checkbox_detection.models import Checkbox

MIN_BOX_SIZE_RATIO = 0.0075
MAX_BOX_SIZE_RATIO = 0.02
MIN_ASPECT_RATIO = 0.65
MAX_ASPECT_RATIO = 1.4
MIN_RECTANGULARITY = 0.75
MIN_INTERIOR_INK_RATIO = 0.08
MIN_THRESHOLD = 200
INK_THRESHOLD = 160


class OpenCVV1CheckboxesDetector:
    """Detect square checkbox regions and infer whether their interiors are marked."""

    def detect(self, image_path: Path) -> list[Checkbox]:
        image_path = Path(image_path)
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unable to read image '{image_path}'")

        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.threshold(
            grayscale, MIN_THRESHOLD, 255, cv2.THRESH_BINARY_INV
        )[1]
        contours, _ = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        min_size = round(grayscale.shape[1] * MIN_BOX_SIZE_RATIO)
        max_size = round(grayscale.shape[1] * MAX_BOX_SIZE_RATIO)
        checkboxes = []
        for contour in contours:
            candidate = self._candidate_box(
                contour,
                min_size=min_size,
                max_size=max_size,
            )
            if candidate is None:
                continue

            x, y, width, height = candidate
            checkboxes.append(
                Checkbox(
                    bbox=(x, y, x + width - 1, y + height - 1),
                    is_checked=self._is_checked(
                        grayscale,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                    ),
                )
            )

        checkboxes.sort(key=lambda checkbox: (checkbox.bbox[1], checkbox.bbox[0]))
        return checkboxes

    @staticmethod
    def _candidate_box(
        contour,
        *,
        min_size: int,
        max_size: int,
    ) -> tuple[int, int, int, int] | None:
        x, y, width, height = cv2.boundingRect(contour)
        if not (min_size <= width <= max_size and min_size <= height <= max_size):
            return None

        aspect_ratio = width / height
        if not MIN_ASPECT_RATIO <= aspect_ratio <= MAX_ASPECT_RATIO:
            return None

        rectangularity = cv2.contourArea(contour) / (width * height)
        if rectangularity < MIN_RECTANGULARITY:
            return None

        perimeter = cv2.arcLength(contour, True)
        vertices = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if not 4 <= len(vertices) <= 8:
            return None

        return x, y, width, height

    @staticmethod
    def _is_checked(
        grayscale,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        margin_x = max(2, width // 4)
        margin_y = max(2, height // 4)
        interior = grayscale[
            y + margin_y : y + height - margin_y,
            x + margin_x : x + width - margin_x,
        ]
        if interior.size == 0:
            return False
        ink_ratio = (interior < INK_THRESHOLD).mean()
        return bool(ink_ratio >= MIN_INTERIOR_INK_RATIO)
