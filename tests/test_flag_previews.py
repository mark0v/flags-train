from pathlib import Path

from PIL import Image

from app.services.flag_previews import (
    PREVIEW_BACKGROUND,
    PREVIEW_HEIGHT,
    PREVIEW_PADDING,
    PREVIEW_WIDTH,
    build_flag_preview,
)


def test_build_flag_preview_creates_consistent_canvas_for_wide_flag(tmp_path: Path) -> None:
    source = tmp_path / "wide.png"
    target = tmp_path / "preview.png"
    Image.new("RGB", (900, 450), (0, 128, 0)).save(source, format="PNG")

    build_flag_preview(source, target)

    with Image.open(target) as preview:
        assert preview.size == (PREVIEW_WIDTH, PREVIEW_HEIGHT)
        assert preview.getpixel((0, 0)) == PREVIEW_BACKGROUND
        assert preview.getpixel((PREVIEW_WIDTH // 2, PREVIEW_HEIGHT // 2)) == (0, 128, 0)


def test_build_flag_preview_preserves_tall_flag_inside_padded_canvas(tmp_path: Path) -> None:
    source = tmp_path / "tall.png"
    target = tmp_path / "preview.png"
    Image.new("RGB", (300, 900), (220, 20, 60)).save(source, format="PNG")

    build_flag_preview(source, target)

    with Image.open(target) as preview:
        assert preview.size == (PREVIEW_WIDTH, PREVIEW_HEIGHT)
        assert preview.getpixel((PREVIEW_PADDING // 2, PREVIEW_HEIGHT // 2)) == PREVIEW_BACKGROUND
        assert preview.getpixel((PREVIEW_WIDTH // 2, PREVIEW_HEIGHT // 2)) == (220, 20, 60)
