from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Shop

from app.repositories.shops import ShopRepository
from app.schemas.shop import ShopCreate


class ShopService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ShopRepository(session)

    async def get(self, shop_uuid) -> Shop | None:
        return await self.repository.get(shop_uuid)

    async def get_by_vendor(self, vendor_uuid) -> Shop | None:
        return await self.repository.get_by_vendor(vendor_uuid)

    async def get_all(self) -> list[Shop]:
        return await self.repository.get_all()

    async def create(self, payload: ShopCreate) -> Shop:
        shops = await self.repository.get_all()
        has_created_shop = await self.get_by_vendor(payload.vendor_uuid)

        if has_created_shop:
            raise ValueError("Vendor shop capacity reached")

        if len(shops) >= 5:
            raise ValueError("System shop capacity reached")

        return await self.repository.create(payload)

    async def update_settings(self, shop_uuid: str, payload: dict) -> dict:
        return await self.repository.update_settings(shop_uuid, payload)
