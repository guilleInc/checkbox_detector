from pydantic import BaseModel

from checkbox_detection import Checkbox


class DetectionResponse(BaseModel):
    boxes: list[Checkbox]
