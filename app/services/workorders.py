from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.db.models import PrintJob
from app.schemas.workorder import PrintJobCreate, PrintJobRead
from app.repositories.workorders import PrintJobRepository


from typing import Union, IO
from pathlib import Path


class PrintJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = PrintJobRepository(session)

    async def get(self, workorder_uuid: str) -> PrintJob | None:
        return await self.repository.get(workorder_uuid)

    async def get_by_customer_uuid(self, customer_uuid: str) -> list[PrintJob]:
        return await self.repository.get_by_customer_uuid(customer_uuid)

    async def get_by_checkout_request_id(
        self, checkout_request_id: str
    ) -> PrintJob | None:
        return await self.repository.get_by_checkout_request_id(checkout_request_id)

    async def get_by_merchant_request_id(
        self, merchant_request_id: str
    ) -> PrintJob | None:
        return await self.repository.get_by_merchant_request_id(merchant_request_id)

    async def get_by_shop_uuid(
        self,
        shop_uuid: str,
        status: str | None = "queued",
    ) -> list[PrintJob]:
        """`status=None` means no filtering."""
        return await self.repository.get_by_shop_uuid(shop_uuid, status)

    async def get_all(self) -> list[PrintJob]:
        return await self.repository.get_all()

    async def create(
        self,
        payload: PrintJobCreate,
        file_object: Union[UploadFile, bytes, str, IO[bytes], Path],
    ) -> PrintJob:
        return await self.repository.create(payload, file_object)
