from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HiddenCountry


class HiddenCountriesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_hidden_country_codes(self, user_id: int) -> list[str]:
        stmt = (
            select(HiddenCountry.country_code)
            .where(HiddenCountry.user_id == user_id)
            .order_by(HiddenCountry.country_code)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def hidden_count(self, user_id: int) -> int:
        stmt = select(func.count(HiddenCountry.id)).where(HiddenCountry.user_id == user_id)
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def hide_country(
        self,
        user_id: int,
        country_code: str,
        *,
        total_country_count: int,
        min_available_countries: int,
    ) -> bool:
        existing_codes = await self.get_hidden_country_codes(user_id)
        if country_code in existing_codes:
            return True
        if total_country_count - (len(existing_codes) + 1) < min_available_countries:
            return False

        self._session.add(HiddenCountry(user_id=user_id, country_code=country_code))
        await self._session.flush()
        return True

    async def reset_hidden_countries(self, user_id: int) -> int:
        count = await self.hidden_count(user_id)
        await self._session.execute(
            delete(HiddenCountry).where(HiddenCountry.user_id == user_id)
        )
        await self._session.flush()
        return count
