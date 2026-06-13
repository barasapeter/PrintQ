from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.workorder import PrintJobRead
from app.services.workorders import PrintJobService

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workorder(
    file: UploadFile = File(...),
    shop_uuid: str = Form(...),
    customer_uuid: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
):
    print(f"Received file: {file.filename}")
    print(f"Shop UUID: {shop_uuid}")
    print(f"Customer UUID: {customer_uuid}")

    service = PrintJobService(session)
    result = await service.create(file, shop_uuid, customer_uuid)
    return result
