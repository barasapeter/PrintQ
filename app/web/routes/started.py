from fastapi import APIRouter, Request, Depends

from app.core.templating import templates

router = APIRouter()


@router.get("/get-started")
async def index(request: Request):
    request.session.pop("customer", None)
    return templates.TemplateResponse("started.html", {"request": request})
