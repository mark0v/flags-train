from __future__ import annotations

from pathlib import Path

import orjson

from app.services.data_pipeline import dataset_summary, validate_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "normalized" / "countries.json"
FLAGS_DIR = PROJECT_ROOT / "data" / "flags"


def main() -> None:
    countries = orjson.loads(DATASET_PATH.read_bytes())
    validate_dataset(countries, FLAGS_DIR)
    summary = dataset_summary(countries)
    print(
        "Dataset is valid. "
        f"Countries: {summary['countries_count']}. "
        f"Range: {summary['first_country_code']} - {summary['last_country_code']}."
    )


if __name__ == "__main__":
    main()
