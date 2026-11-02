from pydantic import BaseModel, model_validator


class Checkbox(BaseModel):
    """A checkbox: bbox is [x1, y1, x2, y2] (top-left and bottom-right pixels, inclusive)."""

    bbox: tuple[int, int, int, int]
    is_checked: bool

    @model_validator(mode="after")
    def check_coordinates(self):
        x1, y1, x2, y2 = self.bbox
        if min(self.bbox) < 0:
            raise ValueError("coordinates must be greater than or equal to 0")
        if x2 < x1:
            raise ValueError("x2 must be greater than or equal to x1")
        if y2 < y1:
            raise ValueError("y2 must be greater than or equal to y1")
        return self
