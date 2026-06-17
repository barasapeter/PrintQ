from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse

from app.schemas.shop import ShopCreate, ShopRead
from app.api.deps import get_db_session
from app.services.shops import ShopService

from app.core.phone import process_phone


router = APIRouter()


@router.post("", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
async def create_shop(
    payload: ShopCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ShopCreate:
    service = ShopService(session)
    processed_phone = process_phone(payload.phone_contact)
    if processed_phone is None:
        return JSONResponse(status_code=400, content={"detail": "Invalid phone number"})
    payload.phone_contact = processed_phone
    return await service.create(payload)


@router.post("/settings", status_code=status.HTTP_200_OK)
async def update_settings(
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    shop_service = ShopService(session)
    shop = await shop_service.get_by_vendor(request.session.get("vendor"))

    return await shop_service.update_settings(
        str(shop.uuid),
        payload,
    )
