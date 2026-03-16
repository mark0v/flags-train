from __future__ import annotations

from pathlib import Path

from app.services.flag_previews import build_flag_preview

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"


def main() -> None:
    png_files = sorted(FLAGS_DIR.glob("*.png"))
    for path in png_files:
        build_flag_preview(path, path)
    print(f"Normalized {len(png_files)} flag previews in {FLAGS_DIR}.")


if __name__ == "__main__":
    main()
