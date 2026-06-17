from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vendor

from app.repositories.vendors import VendorRepository
from app.schemas.vendor import VendorCreate


class VendorService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = VendorRepository(session)

    async def get(self, vendor_uuid) -> Vendor | None:
        return await self.repository.get(vendor_uuid)

    async def get_all(self) -> list[Vendor]:
        return await self.repository.get_all()

    async def get_by_email(self, email_address) -> Vendor | None:
        return await self.repository.get_by_email(email_address)

    async def get_by_username(self, username) -> Vendor | None:
        return await self.repository.get_by_username(username)

    async def create(self, payload: VendorCreate) -> Vendor:
        vendors = await self.repository.get_all()

        if len(vendors) >= 5:
            raise ValueError("Vendor capacity reached")

        return await self.repository.create(payload)
