from pathlib import Path

from app.services.dataset_validation import validate_local_dataset


def test_validate_local_dataset_returns_summary_for_valid_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "countries.json"
    flags_dir = tmp_path / "flags"
    flags_dir.mkdir()
    (flags_dir / "de.svg").write_text("<svg />", encoding="utf-8")
    dataset_path.write_text(
        """
[
  {
    "code": "DEU",
    "localized_name": {"ru": "Германия", "en": "Germany", "de": "Deutschland"},
    "capital": {"ru": "Берлин", "en": "Berlin", "de": "Berlin"},
    "official_language": {"ru": "Немецкий", "en": "German", "de": "Deutsch"},
    "population": 84000000,
    "population_display": {"ru": "84 млн", "en": "84M", "de": "84 Mio."},
    "currency_name": {"ru": "Евро", "en": "Euro", "de": "Euro"},
    "currency_code": "EUR",
    "flag_file": "de.svg"
  }
]
        """.strip(),
        encoding="utf-8",
    )

    report = validate_local_dataset(dataset_path, flags_dir)

    assert report.is_valid is True
    assert report.countries_count == 1
    assert report.first_country_code == "DEU"
    assert report.last_country_code == "DEU"


def test_validate_local_dataset_returns_error_for_invalid_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "countries.json"
    flags_dir = tmp_path / "flags"
    flags_dir.mkdir()
    dataset_path.write_text("[]", encoding="utf-8")

    report = validate_local_dataset(dataset_path, flags_dir)

    assert report.is_valid is False
    assert report.error == "Dataset is empty."
