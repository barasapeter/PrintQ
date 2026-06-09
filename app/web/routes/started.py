from fastapi import APIRouter, Request, HTTPException

from app.core.templating import templates

router = APIRouter()


@router.get("/get-started")
async def index(request: Request):
    return templates.TemplateResponse(
        "started.html", {"request": request, "status": "let's GO!"}
    )
