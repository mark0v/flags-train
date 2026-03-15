from dataclasses import dataclass
from pathlib import Path

import orjson

from app.constants import SupportedLanguage


@dataclass(slots=True)
class Country:
    code: str
    localized_name: dict[str, str]
    capital: dict[str, str]
    official_language: dict[str, str]
    population: int
    population_display: dict[str, str]
    currency_name: dict[str, str]
    currency_code: str
    flag_file: str

    def name(self, language: SupportedLanguage) -> str:
        return self.localized_name.get(language.value) or self.localized_name[
            SupportedLanguage.EN.value
        ]

    def capital_name(self, language: SupportedLanguage) -> str:
        return self.capital.get(language.value) or self.capital[SupportedLanguage.EN.value]

    def language_name(self, language: SupportedLanguage) -> str:
        return self.official_language.get(language.value) or self.official_language[
            SupportedLanguage.EN.value
        ]

    def currency_label(self, language: SupportedLanguage) -> str:
        return self.currency_name.get(language.value) or self.currency_name[
            SupportedLanguage.EN.value
        ]

    def population_label(self, language: SupportedLanguage) -> str:
        return self.population_display.get(language.value) or self.population_display[
            SupportedLanguage.EN.value
        ]


class CountryStore:
    def __init__(self, countries: list[Country], flags_dir: Path) -> None:
        if not countries:
            raise ValueError("Country dataset is empty. Run the data pipeline first.")
        self._countries = countries
        self._flags_dir = flags_dir

    @classmethod
    def from_path(cls, dataset_path: Path, flags_dir: Path) -> "CountryStore":
        raw = orjson.loads(dataset_path.read_bytes())
        countries = [Country(**item) for item in raw]
        return cls(countries=countries, flags_dir=flags_dir)

    @property
    def countries(self) -> list[Country]:
        return list(self._countries)

    def flag_path(self, country: Country) -> Path:
        return self._flags_dir / country.flag_file
