from app.core.templating import templates


from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.db.models import Customer

from app.services.vendors import VendorService
from app.services.shops import ShopService


router = APIRouter()


@router.get("/get-started")
async def index(request: Request):
    request.session.pop("customer", None)
    return templates.TemplateResponse("started.html", {"request": request})


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    # TODO: Split into a layered architecture
    stmt = select(Customer).where(Customer.uuid == request.session.get("customer"))
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    # TODO: Split into a layered architecture

    shop_service = ShopService(db)
    shops = await shop_service.get_all()

    if not customer:
        return RedirectResponse(url="/get-started")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "phone": customer.properties.get("phone"),
            "shops": shops,
            "customer_uuid": customer.uuid
        },
    )


@router.get("/vendor-signup")
async def vendor_signup(
    request: Request,
):
    return templates.TemplateResponse(
        "vendor-signup.html",
        {"request": request},
    )


@router.get("/shop-create")
async def shop_create(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    service = VendorService(session)
    vendors = await service.get_all()
    return templates.TemplateResponse(
        "shop-create.html",
        {"request": request, "vendors": vendors},
    )
