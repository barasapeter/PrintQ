from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Request
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
    payload = PrintJobCreate(
        shop_uuid=shop_uuid, customer_uuid=customer_uuid, properties={}
    )

    service = PrintJobService(session)
    result = await service.create(payload, file_object)

    return result


@router.post("/queue", status_code=status.HTTP_200_OK)
async def push_to_queue(
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    queue_service = PrintJobService(session)
    return await queue_service.push_to_queue(payload)
