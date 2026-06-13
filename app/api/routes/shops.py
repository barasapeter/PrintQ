from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.schemas.shop import ShopCreate, ShopRead
from app.api.deps import get_db_session
from app.services.shops import ShopService

from app.core.phone import process_phone

import json

router = APIRouter()


@router.post("", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
async def create_shop(
    payload: ShopCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ShopCreate:
    service = ShopService(session)
    processed_phone = process_phone(payload.phone_contact)
    if processed_phone is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid phone number"}
        )

    return await service.create(payload)
