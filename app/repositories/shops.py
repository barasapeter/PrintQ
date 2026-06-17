from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Shop
from app.schemas.shop import ShopCreate

from fastapi import HTTPException

from sqlalchemy.orm.attributes import flag_modified


class ShopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, shop_uuid: str) -> Shop | None:
        return await self.session.get(Shop, shop_uuid)

    async def get_by_vendor(self, vendor_uuid: str) -> Shop | None:
        result = await self.session.execute(
            select(Shop).where(Shop.vendor_uuid == vendor_uuid)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Shop]:
        result = await self.session.execute(select(Shop))
        return list(result.scalars().all())

    async def create(self, payload: ShopCreate) -> Shop:
        shop = Shop(**payload.model_dump())
        self.session.add(shop)
        await self.session.commit()
        await self.session.refresh(shop)
        return shop

    async def update_settings(self, shop_uuid: str, payload: dict) -> dict:
        shop = await self.get(shop_uuid)
        if not shop:
            raise HTTPException(f"Shop {shop_uuid} does not exist")

        shop.properties["print_preferences"] = payload
        self.session.add(shop)
        flag_modified(shop, "properties")
        await self.session.commit()
        await self.session.refresh(shop)
        return {
            "detail": "Print preferences updated successfully",
            "properties": shop.properties,
        }
