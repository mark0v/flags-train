from __future__ import annotations

from pathlib import Path

from app.services.dataset_validation import validate_local_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "normalized" / "countries.json"
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"


def main() -> None:
    report = validate_local_dataset(DATASET_PATH, FLAGS_DIR)
    if not report.is_valid:
        raise SystemExit(report.error or "Dataset validation failed.")

    print(
        "Dataset is valid. "
        f"Countries: {report.countries_count}. "
        f"Range: {report.first_country_code} - {report.last_country_code}."
    )


if __name__ == "__main__":
    main()
