from dataclasses import dataclass
from pathlib import Path

from app.services.country_store import CountryStore


@dataclass(slots=True)
class CatalogHealthReport:
    dataset_count: int
    db_count: int
    missing_in_db: list[str]
    stale_in_db: list[str]
    missing_flag_files: list[str]

    @property
    def is_healthy(self) -> bool:
        return not self.missing_in_db and not self.stale_in_db and not self.missing_flag_files


def build_catalog_health_report(
    store: CountryStore,
    db_codes: list[str],
    flags_dir: Path,
) -> CatalogHealthReport:
    dataset_codes = [country.code for country in store.countries]
    dataset_code_set = set(dataset_codes)
    db_code_set = set(db_codes)

    missing_in_db = sorted(dataset_code_set - db_code_set)
    stale_in_db = sorted(db_code_set - dataset_code_set)
    missing_flag_files = sorted(
        country.code
        for country in store.countries
        if not (flags_dir / country.flag_file).exists()
    )

    return CatalogHealthReport(
        dataset_count=len(dataset_codes),
        db_count=len(db_codes),
        missing_in_db=missing_in_db,
        stale_in_db=stale_in_db,
        missing_flag_files=missing_flag_files,
    )
