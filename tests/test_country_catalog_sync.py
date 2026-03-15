from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.repositories.countries import CountryCatalogRepository
from app.services.country_catalog_sync import sync_country_catalog
from app.services.country_store import CountryStore


async def test_sync_country_catalog_copies_local_dataset_into_db() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    store = CountryStore.from_path(
        Path("tests/fixtures/countries.json"),
        Path("tests/fixtures"),
    )

    async with session_factory() as session:
        repository = CountryCatalogRepository(session)
        synced_count = await sync_country_catalog(repository, store)
        await session.commit()

        codes = await repository.list_codes()

    await engine.dispose()

    assert synced_count == 6
    assert "DEU" in codes
    assert "UKR" in codes
