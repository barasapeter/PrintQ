from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PrintJob
from app.schemas.workorder import PrintJobCreate
from app.services.shops import ShopService
from app.services.workorders import PrintJobService
from app.services.vendors import VendorService
from app.core.storage import FileStorage
from typing import Union, IO
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from fastapi import UploadFile
from app.core.pages import count_pages

from app.db.models import Customer, Shop
from app.core.phone import process_phone
from app.core.c2b import utils_initiate_stk_push
from sqlalchemy.orm import joinedload


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
            stmt = stmt.where(
                PrintJob.properties["status"].astext == status,
                PrintJob.amount.is_not(None),
            )

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

        shop_service = ShopService(self.session)
        shop = await shop_service.get(payload.shop_uuid)
        if not shop:
            raise HTTPException(f"Shop {payload.shop_uuid} does not exist")

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
        printjob.properties["tariffs"] = shop.properties.get(
            "print_preferences",
            {
                "cost_per_page_bw": 5,
                "cost_per_page_color": 10,
                "binding": {
                    "type": "staple",
                    "costs": {"staple": 0, "spiral": 50, "tape": 30},
                },
                "discount": {
                    "enabled": False,
                    "min_pages": 20,
                    "percent": 10,
                    "apply_to": "both",
                },
                "paper_sizes": ["A4", "Letter"],
            },
        )
        self.session.add(printjob)
        await self.session.commit()
        await self.session.refresh(printjob)

        return printjob

    async def push_to_queue(self, origin: str, payload: dict) -> dict:
        client_preferences = payload["settings"]
        printjob = await self.get(payload["printjob_uuid"])
        tariffs = printjob.properties["tariffs"]
        file_metadata = printjob.properties["file_metadata"]

        color_mode = client_preferences["color_mode"]
        copies = client_preferences["copies"]
        binding_type = client_preferences["binding"]
        page_range = client_preferences.get("page_range", "All")

        if await self.verify_payment(str(printjob.uuid)):
            return await self.get_payment_status(printjob.uuid)

        total_pages = file_metadata["page_count"]
        if page_range != "All":
            total_pages = self._get_pages_in_range(total_pages, page_range)
        total_pages *= copies

        cost_per_page = (
            tariffs["cost_per_page_color"]
            if color_mode == "color"
            else tariffs["cost_per_page_bw"]
        )
        printing_cost = total_pages * cost_per_page

        binding_costs = tariffs["binding"]["costs"]
        binding_cost_per_copy = binding_costs.get(binding_type, 0)
        binding_cost = copies * binding_cost_per_copy

        discount = 0
        discount_config = tariffs["discount"]
        if discount_config["enabled"] and total_pages >= discount_config["min_pages"]:
            discount = int(
                (discount_config["percent"] / 100) * (printing_cost + binding_cost)
            )

        total_cost = printing_cost + binding_cost - discount

        stmt = select(Customer).where(Customer.uuid == printjob.customer_uuid)
        result = await self.session.execute(stmt)
        customer = result.scalar_one_or_none()
        phone = process_phone(payload.get("phone", customer.properties["phone"]))

        if phone is None:
            raise ValueError("A valid phone number is required.")

        printjob.properties["queue_metadata"] = {
            "color_mode": color_mode,
            "copies": copies,
            "binding_type": binding_type,
            "page_range": page_range,
            "total_pages": total_pages,
            "cost_per_page": cost_per_page,
            "printing_cost": printing_cost,
            "binding_cost_per_copy": binding_cost_per_copy,
            "binding_cost": binding_cost,
            "discount": discount,
            "total_cost": total_cost,
            "prompt_phone": phone,
        }

        stk = await utils_initiate_stk_push(
            phone, total_cost, origin + "/api/v1/workorder/callback"
        )
        if not stk["success"]:
            print("STK RESPONSE:", stk)
            raise RuntimeError("Failed to initiate payment")

        printjob.checkout_request_id = stk["detail"]["CheckoutRequestID"]
        printjob.merchant_request_id = stk["detail"]["MerchantRequestID"]
        printjob.result_desc = None

        # For Testing Only
        import platform, json

        if platform.system() == "Windows":
            data = {
                "CheckoutRequestID": stk["detail"]["CheckoutRequestID"],
                "amount": total_cost,
            }
            with open("CheckoutRequestID.json", "w") as f:
                json.dump(data, f, indent=4)

        self.session.add(printjob)
        flag_modified(printjob, "properties")
        await self.session.commit()
        await self.session.refresh(printjob)

        return await self.get_payment_status(printjob.uuid)

    def _get_pages_in_range(self, total_pages: int, page_range: str) -> int:
        if "-" in page_range:
            start, end = map(int, page_range.split("-"))
            return max(0, min(end, total_pages) - start + 1)
        elif "," in page_range:
            pages = [int(p.strip()) for p in page_range.split(",")]
            return len([p for p in pages if 1 <= p <= total_pages])
        return total_pages

    async def callback(self, payload: dict) -> dict:
        result_code: str = payload["Body"]["stkCallback"]["ResultCode"]
        checkout_request_id = payload["Body"]["stkCallback"]["CheckoutRequestID"]
        result_desc: str = payload["Body"]["stkCallback"]["ResultDesc"]

        printjob = await self.get_by_checkout_request_id(checkout_request_id)

        if not printjob:
            raise ValueError(
                f"No printjob found for checkout_request_id={checkout_request_id}"
            )

        receipt_number = None
        if result_code == 0:
            items = payload["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
            amount = next((i["Value"] for i in items if i["Name"] == "Amount"), None)
            receipt_number = next(
                (i["Value"] for i in items if i["Name"] == "MpesaReceiptNumber"), None
            )
            phone_number = next(
                (i["Value"] for i in items if i["Name"] == "PhoneNumber"), None
            )

            printjob.amount = amount
            printjob.properties["stkcallback_metadata"] = {
                "receipt_number": receipt_number,
                "phone_number": phone_number,
                "callback_detail": payload,
            }
            printjob.properties["status"] = "Queued"

        printjob.result_desc = result_desc
        flag_modified(printjob, "properties")
        await self.session.commit()
        await self.session.refresh(printjob)

        return {"detail": "Callback: 'OK'"}

    async def verify_payment(self, printjob_uuid: str) -> bool:
        printjob = await self.get(printjob_uuid)

        amount = printjob.amount is not None
        metadata_saved = printjob.properties.get("stkcallback_metadata")

        if amount and metadata_saved:
            return True

        return False

    async def get_payment_status(self, printjob_uuid: str) -> dict:
        printjob = await self.get(printjob_uuid)
        return {
            "amount": int(printjob.amount) if printjob.amount is not None else None,
            "result_desc": printjob.result_desc,
        }

    async def set_print_intent(self, printjob_uuid: str) -> None:
        printjob = await self.get(printjob_uuid)
        shop = printjob.shop
        vendor = shop.vendor
        vendor.properties["print_intent"] = printjob_uuid

        flag_modified(vendor, "properties")
        await self.session.commit()
        await self.session.refresh(vendor)

        return None

    async def clear_print_intent(self, printjob_uuid: str) -> None:
        printjob = await self.get(printjob_uuid)
        shop = printjob.shop
        vendor = shop.vendor
        vendor.properties.pop("print_intent", None)

        flag_modified(vendor, "properties")
        await self.session.commit()
        await self.session.refresh(vendor)

        return None

    async def get_print_intent(self, vendor_uuid: str) -> PrintJob:
        vendor_service = VendorService(self.session)
        vendor = await vendor_service.get(vendor_uuid)

        printjob = await self.get(printjob_uuid)

