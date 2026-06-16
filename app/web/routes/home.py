from fastapi import APIRouter, Request, HTTPException

from app.core.templating import templates

router = APIRouter()


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )
