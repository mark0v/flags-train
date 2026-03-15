from dataclasses import dataclass

from app.db.models import CountryCatalog
from app.services.country_store import CountryStore


@dataclass(slots=True)
class CatalogSyncPreview:
    dataset_count: int
    db_count: int
    to_create: list[str]
    to_update: list[str]
    to_delete: list[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.to_create or self.to_update or self.to_delete)


def build_catalog_sync_preview(
    store: CountryStore,
    db_countries: list[CountryCatalog],
) -> CatalogSyncPreview:
    dataset_by_code = {country.code: country for country in store.countries}
    db_by_code = {country.code: country for country in db_countries}

    to_create = sorted(set(dataset_by_code) - set(db_by_code))
    to_delete = sorted(set(db_by_code) - set(dataset_by_code))
    to_update = sorted(
        code
        for code in set(dataset_by_code) & set(db_by_code)
        if _has_country_changes(dataset_by_code[code], db_by_code[code])
    )

    return CatalogSyncPreview(
        dataset_count=len(dataset_by_code),
        db_count=len(db_by_code),
        to_create=to_create,
        to_update=to_update,
        to_delete=to_delete,
    )


def _has_country_changes(dataset_country: object, db_country: CountryCatalog) -> bool:
    return any(
        [
            dataset_country.localized_name != db_country.localized_name,
            dataset_country.capital != db_country.capital,
            dataset_country.official_language != db_country.official_language,
            dataset_country.population != db_country.population,
            dataset_country.population_display != db_country.population_display,
            dataset_country.currency_name != db_country.currency_name,
            dataset_country.currency_code != db_country.currency_code,
            dataset_country.flag_file != db_country.flag_file,
        ]
    )
