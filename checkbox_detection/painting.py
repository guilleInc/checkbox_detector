from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from checkbox_detection.models import Checkbox


class CheckboxPainter:
    def __init__(
        self,
        output_dir: Path,
        checked_color: str = "#00FF00",
        unchecked_color: str = "#FF0000",
        opacity: float = 0.4,  # 0.0 (invisible) to 1.0 (opaque)
    ):
        self.output_dir = Path(output_dir)
        self.checked_color = checked_color
        self.unchecked_color = unchecked_color
        self.opacity = opacity

    def paint(self, image_path: Path, checkboxes: list[Checkbox]) -> Path:
        """Save a copy of the image with the checkboxes painted over it.

        The copy is written to `self.output_dir` as <name>_painted<ext>; the
        original image is never modified. Returns the path of the saved image.
        """
        image_path = Path(image_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{image_path.stem}_painted{image_path.suffix}"
        if output_path.exists() and output_path.samefile(image_path):
            raise ValueError("output path would overwrite the original image")

        with Image.open(image_path) as original:
            base = original.convert("RGBA")
            has_alpha = (
                original.mode in ("RGBA", "LA", "PA") or "transparency" in original.info
            )

        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        alpha = round(self.opacity * 255)
        for box in checkboxes:
            color = self.checked_color if box.is_checked else self.unchecked_color
            fill = (*ImageColor.getrgb(color)[:3], alpha)
            draw.rectangle(list(box.bbox), fill=fill)

        result = Image.alpha_composite(base, overlay)
        # Formats like JPEG can't store transparency.
        if not has_alpha:
            result = result.convert("RGB")
        result.save(output_path)
        return output_path
