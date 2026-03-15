from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CountryCatalog
from app.services.country_store import Country


class CountryCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_codes(self) -> list[str]:
        result = await self._session.execute(select(CountryCatalog.code))
        return [row[0] for row in result.all()]

    async def upsert_many(self, countries: list[Country]) -> None:
        existing_codes = set(await self.list_codes())
        incoming_codes = {country.code for country in countries}

        for country in countries:
            catalog_country = await self._session.get(CountryCatalog, country.code)
            if catalog_country is None:
                catalog_country = CountryCatalog(code=country.code)
                self._session.add(catalog_country)

            catalog_country.localized_name = country.localized_name
            catalog_country.capital = country.capital
            catalog_country.official_language = country.official_language
            catalog_country.population = country.population
            catalog_country.population_display = country.population_display
            catalog_country.currency_name = country.currency_name
            catalog_country.currency_code = country.currency_code
            catalog_country.flag_file = country.flag_file

        stale_codes = existing_codes - incoming_codes
        if stale_codes:
            await self._session.execute(
                delete(CountryCatalog).where(CountryCatalog.code.in_(stale_codes))
            )

        await self._session.flush()

    async def count(self) -> int:
        return len(await self.list_codes())

    async def summary(self) -> dict[str, int]:
        count = await self.count()
        return {"countries_count": count}
