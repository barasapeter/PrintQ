from fastapi import APIRouter

router = APIRouter()


@router.post("/send")
async def send() -> dict[str, str]:
    return {"status": "ok"}
