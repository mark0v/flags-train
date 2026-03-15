from pathlib import Path

from app.services.catalog_health import build_catalog_health_report
from app.services.country_store import CountryStore


def test_catalog_health_report_detects_db_and_flag_gaps(tmp_path: Path) -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )
    report = build_catalog_health_report(
        store=store,
        db_codes=["DEU", "FRA", "XXX"],
        flags_dir=tmp_path,
    )

    assert report.dataset_count == 6
    assert report.db_count == 3
    assert "ESP" in report.missing_in_db
    assert report.stale_in_db == ["XXX"]
    assert "DEU" in report.missing_flag_files
    assert report.is_healthy is False


def test_catalog_health_report_is_healthy_when_all_codes_and_flags_exist(tmp_path: Path) -> None:
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        tmp_path,
    )
    for country in store.countries:
        (tmp_path / country.flag_file).write_text("<svg />", encoding="utf-8")

    report = build_catalog_health_report(
        store=store,
        db_codes=[country.code for country in store.countries],
        flags_dir=tmp_path,
    )

    assert report.is_healthy is True
