from app.core.templating import templates


from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.db.models import Customer

from app.services.vendors import VendorService
from app.services.shops import ShopService
from app.services.workorders import PrintJobService
from app.core.templating import get_file_icon, format_file_size, time_ago
from app.core.templating import time_ago

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    customer_uuid = request.session.get("customer")
    # TODO: Split into a layered architecture
    stmt = select(Customer).where(Customer.uuid == customer_uuid)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    # TODO: Split into a layered architecture

    shop_service = ShopService(db)
    shops = await shop_service.get_all()

    printjob_service = PrintJobService(db)
    printjobs = await printjob_service.get_by_customer_uuid(customer_uuid)

    if not customer:
        return RedirectResponse(url="/otplogin")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "phone": customer.properties.get("phone"),
            "shops": shops,
            "customer_uuid": customer.uuid,
            "printjobs": printjobs,
            "get_file_icon": get_file_icon,
            "format_file_size": format_file_size,
            "time_ago": time_ago,
        },
    )


@router.get("/otplogin")
async def otplogin(request: Request):
    request.session.pop("customer", None)
    return templates.TemplateResponse("started.html", {"request": request})


@router.get("/settings")
async def settings(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    if not request.session.get("vendor"):
        return RedirectResponse("/vendor/login")

    shop_service = ShopService(session)
    shop = await shop_service.get_by_vendor(request.session.get("vendor"))

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "print_preferences": shop.properties.get("print_preferences", {}),
        },
    )


@router.get("/vendor")
async def vendor(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    vendor_uuid = request.session.get("vendor")
    vendor_service = VendorService(session)
    vendor = await vendor_service.get(vendor_uuid)
    if not vendor:
        return RedirectResponse("/vendor/login")

    shop_service = ShopService(session)
    shop = await shop_service.get_by_vendor(vendor_uuid)

    if not shop:
        workorders = None
    else:
        workorder_service = PrintJobService(session)
        workorders = await workorder_service.get_by_shop_uuid(shop.uuid, "Queued")

    show_intent_dialog = False
    if request.session.get("print_intent"):
        show_intent_dialog = True

    return templates.TemplateResponse(
        "vendor.html",
        {
            "request": request,
            "workorders": workorders,
            "time_ago": time_ago,
            "show_intent_dialog": show_intent_dialog
        },
    )


@router.get("/vendor/login")
async def vendor_login(
    request: Request,
):
    return templates.TemplateResponse(
        "vendor-login.html",
        {"request": request},
    )


@router.get("/vendor/signup")
async def vendor_signup(
    request: Request,
):
    return templates.TemplateResponse(
        "vendor-signup.html",
        {"request": request},
    )


@router.get("/shop/create")
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
