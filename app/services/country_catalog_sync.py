from app.repositories.countries import CountryCatalogRepository
from app.services.country_store import CountryStore


async def sync_country_catalog(
    repository: CountryCatalogRepository,
    store: CountryStore,
) -> int:
    await repository.upsert_many(store.countries)
    return await repository.count()
