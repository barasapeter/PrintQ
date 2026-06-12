from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, HTTPException, Depends, status


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
    existing_vendor = await service.get_by_email(payload.email_address)

    if existing_vendor is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )
    
    return await service.create(payload)