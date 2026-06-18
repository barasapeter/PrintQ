from app.core.templating import templates


from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.db.models import Customer

from app.services.vendors import VendorService
from app.services.shops import ShopService
from app.services.workorders import PrintJobService
from app.core.templating import get_file_icon, format_file_size, time_ago
from app.core.dtypes import validate_document


router = APIRouter()


@router.get("/queue/{printjob_uuid}")
async def index(
    request: Request,
    printjob_uuid: str,
    db: AsyncSession = Depends(get_db_session),
):
    printjob_service = PrintJobService(db)
    printjob = await printjob_service.get(printjob_uuid)
    if str(printjob.customer_uuid) != request.session.get("customer"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden, you do not have permission to access this resource.",
        )
    printjob.filetype = validate_document(
        printjob.properties["file_metadata"]["filepath"]
    )
    # printjob.preview_image_url = (
    #     "https://pbs.twimg.com/media/HK86MFXXkAAjq8J?format=jpg&name=small"
    # )
    shop_service = ShopService(db)
    shop = await shop_service.get(str(printjob.shop_uuid))

    return templates.TemplateResponse(
        "queue.html",
        {
            "request": request,
            "printjob": printjob,
            "format_file_size": format_file_size,
            "get_file_icon": get_file_icon,
            "time_ago": time_ago,
            "shop": shop,
            "tariff": printjob.properties.get("tariffs"),
            "payment_completed": await printjob_service.verify_payment(
                str(printjob.uuid)
            ),
        },
    )
