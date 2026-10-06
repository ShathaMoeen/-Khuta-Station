from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import StationNotFoundError
from app.db.models import Station


class StationRepository:
    async def get(self, session: AsyncSession, station_id: int) -> Station:
        station=await session.get(Station,station_id)
        if station is None:
            raise StationNotFoundError('Unknown station')
        return station

    async def list(self, session: AsyncSession) -> list[Station]:
        return list((await session.scalars(select(Station).order_by(Station.id))).all())


class ExhibitionRepository:
    """API-facing repository returning stable response dictionaries."""
    def __init__(self):
        self.stations=StationRepository()

    async def station(self, session: AsyncSession, station_id: int) -> dict:
        row=await self.stations.get(session,station_id)
        return {'id':row.id,'code':row.code,'name':row.name,'topic':row.topic,'location':row.location}

    async def list_stations(self, session: AsyncSession) -> list[dict]:
        return [{'id':r.id,'code':r.code,'name':r.name,'topic':r.topic,'location':r.location} for r in await self.stations.list(session)]

