from app.core.templating import templates


from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.db.models import Customer


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
    stmt = select(Customer).where(Customer.uuid == request.session.get("customer"))
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        return RedirectResponse(url="/get-started")

    return templates.TemplateResponse("dashboard.html", {"request": request, "phone": customer.properties.get("phone")})
