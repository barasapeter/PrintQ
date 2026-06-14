from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.workorder import PrintJobCreate, PrintJobRead
from app.services.workorders import PrintJobService

router = APIRouter()


@router.post("", response_model=PrintJobRead, status_code=status.HTTP_201_CREATED)
async def create_workorder(
    file_object: UploadFile = File(...),
    shop_uuid: str = Form(...),
    customer_uuid: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
) -> PrintJobRead:
    """
    Sequence of statuses:
        Uploaded
        ↓
        Awaiting Payment
        ↓
        Paid
        ↓
        Processing
        ↓
        Queued
        ↓
        Printing
        ↓
        Printed
        ↓
        Ready for Pickup
        ↓
        Completed
    """

    payload = PrintJobCreate(
        shop_uuid=shop_uuid, customer_uuid=customer_uuid, properties={}
    )

    service = PrintJobService(session)
    result = await service.create(payload, file_object)

    return result
