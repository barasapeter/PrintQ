from fastapi import APIRouter, Request, HTTPException

from app.core.templating import templates

router = APIRouter()


@router.get("/")
async def index(request: Request):
    raise HTTPException(status_code=403, detail="Sample")
    return templates.TemplateResponse(
        "index.html", {"request": request, "status": "let's GO!"}
    )
