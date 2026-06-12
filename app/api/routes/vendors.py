from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.core.security import hash_password

from app.schemas.vendor import VendorCreate, VendorRead
from app.api.deps import get_db_session
from app.services.vendors import VendorService

router = APIRouter()


@router.post("", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    session: AsyncSession = Depends(get_db_session),
) -> VendorRead:
    service = VendorService(session)
    existing_vendor_email, existing_vendor_username = await service.get_by_email(
        payload.email_address
    ), await service.get_by_username(payload.username)

    if existing_vendor_email is not None or existing_vendor_username is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": f"A user with this {"email address" if existing_vendor_email else "username"} already exists."
            },
        )

    payload.password_hash = hash_password(payload.password_hash)

    return await service.create(payload)
