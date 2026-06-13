from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PrintJob
from app.schemas.workorder import PrintJobCreate

from app.repositories.workorders import PrintJobRepository
from app.core.storage import FileStorage
from fastapi import UploadFile
from pathlib import Path
import uuid

from app.schemas.workorder import PrintJobRead


class PrintJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = PrintJobRepository(session)

    async def get(self, workorder_uuid: str) -> PrintJob | None:
        return await self.repository.get(PrintJob, workorder_uuid)

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
        return await self.repository.get_orders_by_shop_uuid(shop_uuid, status)

    async def get_all(self) -> list[PrintJob]:
        return await self.repository.get_all()

    async def create(self, file: UploadFile, shop_uuid: str, customer_uuid: str):
        # Debug: print file type
        print(f"File type in service: {type(file)}")
        print(f"File has 'read' attribute: {hasattr(file, 'read')}")
        print(f"File has 'filename' attribute: {hasattr(file, 'filename')}")

        # Create absolute path for storage
        base_storage_path = Path("storage")
        base_storage_path.mkdir(parents=True, exist_ok=True)

        customer_dir = f"storage/{customer_uuid}/"

        # Create customer directory if it doesn't exist
        Path(customer_dir).mkdir(parents=True, exist_ok=True)

        file_storage = FileStorage(customer_dir)

        # Generate unique filename with original extension
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # Save the file
        saved_path = await file_storage.save(file, unique_filename)

        print(f"File saved to: {saved_path}")
        print(f"File exists: {Path(saved_path).exists()}")

        # Now create your work order record
        # Example:
        # workorder = PrintJob(
        #     shop_uuid=shop_uuid,
        #     customer_uuid=customer_uuid,
        #     file_path=saved_path,
        #     file_name=file.filename,
        #     file_size=file.size,
        #     status="pending"
        # )
        # self.session.add(workorder)
        # await self.session.commit()
        # await self.session.refresh(workorder)
        # return workorder

        # Temporary return for testing
        return {
            "id": 1,
            "shop_uuid": shop_uuid,
            "customer_uuid": customer_uuid,
            "file_path": saved_path,
            "file_name": file.filename,
            "status": "pending",
        }
