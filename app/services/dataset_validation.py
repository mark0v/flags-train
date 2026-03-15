from dataclasses import dataclass
from pathlib import Path

import orjson

from app.services.data_pipeline import dataset_summary, validate_dataset


@dataclass(slots=True)
class DatasetValidationReport:
    is_valid: bool
    countries_count: int = 0
    first_country_code: str = "-"
    last_country_code: str = "-"
    error: str | None = None


def validate_local_dataset(dataset_path: Path, flags_dir: Path) -> DatasetValidationReport:
    try:
        countries = orjson.loads(dataset_path.read_bytes())
        validate_dataset(countries, flags_dir)
        summary = dataset_summary(countries)
        return DatasetValidationReport(
            is_valid=True,
            countries_count=int(summary["countries_count"]),
            first_country_code=str(summary["first_country_code"]),
            last_country_code=str(summary["last_country_code"]),
        )
    except Exception as exc:
        return DatasetValidationReport(is_valid=False, error=str(exc))
