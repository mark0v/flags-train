from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:
    vendor_path = Path(__file__).resolve().parents[2] / ".vendor"
    if vendor_path.exists():
        sys.path.insert(0, str(vendor_path))
        from PIL import Image
    else:
        raise

PREVIEW_WIDTH = 1600
PREVIEW_HEIGHT = 1000
PREVIEW_PADDING = 48
PREVIEW_BACKGROUND = (255, 255, 255)


def build_flag_preview(
    source_path: Path,
    target_path: Path,
    *,
    width: int = PREVIEW_WIDTH,
    height: int = PREVIEW_HEIGHT,
    padding: int = PREVIEW_PADDING,
) -> None:
    with Image.open(source_path) as source:
        image = source.convert("RGBA")

    inner_width = max(width - padding * 2, 1)
    inner_height = max(height - padding * 2, 1)
    image.thumbnail((inner_width, inner_height), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (width, height), PREVIEW_BACKGROUND + (255,))
    offset = ((width - image.width) // 2, (height - image.height) // 2)
    canvas.alpha_composite(image, dest=offset)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(target_path, format="PNG", optimize=True)
