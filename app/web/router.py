from fastapi import APIRouter

from app.web.routes import home, queues, usage

home_router = APIRouter()

home_router.include_router(home.router, prefix="", tags=["home"])
home_router.include_router(usage.router, prefix="", tags=["started"])
home_router.include_router(queues.router, prefix="", tags=["queues"])
