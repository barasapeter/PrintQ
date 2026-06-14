from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vendor
from app.schemas.vendor import VendorCreate


class VendorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, vendor_uuid: str) -> Vendor | None:
        return await self.session.get(Vendor, vendor_uuid)

    async def get_by_email(self, email_address: str) -> Vendor | None:
        result = await self.session.execute(
            select(Vendor).where(Vendor.email_address == email_address)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Vendor | None:
        result = await self.session.execute(
            select(Vendor).where(Vendor.username == username)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Vendor]:
        result = await self.session.execute(select(Vendor))
        return list(result.scalars().all())

    async def create(self, payload: VendorCreate) -> Vendor:
        vendor = Vendor(**payload.model_dump())
        self.session.add(vendor)
        await self.session.commit()
        await self.session.refresh(vendor)
        return vendor
