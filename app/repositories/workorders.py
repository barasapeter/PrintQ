from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PrintJob
from app.schemas.workorder import PrintJobCreate
from app.core.storage import FileStorage
from typing import Union, IO
from pathlib import Path

from fastapi import UploadFile
from app.core.pages import count_pages


class PrintJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, workorder_uuid: str) -> PrintJob | None:
        return await self.session.get(PrintJob, workorder_uuid)

    async def get_by_customer_uuid(self, customer_uuid: str) -> list[PrintJob]:
        result = await self.session.execute(
            select(PrintJob)
            .where(PrintJob.customer_uuid == customer_uuid)
            .order_by(PrintJob.updated_at.desc())
        )
        return result.scalars().all()

    async def get_by_checkout_request_id(
        self, checkout_request_id: str
    ) -> PrintJob | None:
        result = await self.session.execute(
            select(PrintJob).where(PrintJob.checkout_request_id == checkout_request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_merchant_request_id(
        self, merchant_request_id: str
    ) -> PrintJob | None:
        result = await self.session.execute(
            select(PrintJob).where(PrintJob.merchant_request_id == merchant_request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_shop_uuid(
        self,
        shop_uuid: str,
        status: str | None = None,
    ) -> list[PrintJob]:
        """`status=None` means no filtering."""
        stmt = select(PrintJob).where(PrintJob.shop_uuid == shop_uuid)

        if status is not None:
            stmt = stmt.where(PrintJob.properties["status"].astext == status)

        stmt = stmt.order_by(PrintJob.updated_at.asc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all(self) -> list[PrintJob]:
        result = await self.session.execute(select(PrintJob))
        return list(result.scalars().all())

    async def create(
        self,
        payload: PrintJobCreate,
        file_object: Union[UploadFile, bytes, str, IO[bytes], Path],
    ) -> PrintJob:
        file_storage = FileStorage(f"storage/{payload.customer_uuid}")

        saved_path = await file_storage.save(file_object, payload.uuid)

        file_metadata = {
            "filepath": saved_path,
            "filename": file_object.filename,
            "filesize": getattr(file_object, "size", None),
            "page_count": count_pages(saved_path),
        }

        printjob = PrintJob(**payload.model_dump())
        printjob.properties["status"] = "Uploaded"
        # Sequence of statuses:
        #     Uploaded
        #     ↓
        #     Awaiting Payment
        #     ↓
        #     Paid
        #     ↓
        #     Queued
        #     ↓
        #     Printing
        #     ↓
        #     Printed
        #     ↓
        #     Ready for Pickup
        #     ↓
        #     Completed
        printjob.properties["file_metadata"] = file_metadata
        self.session.add(printjob)
        await self.session.commit()
        await self.session.refresh(printjob)

        return printjob
