from fastapi import APIRouter

from app.web.routes import home, started, queues

home_router = APIRouter()

home_router.include_router(home.router, prefix="", tags=["home"])
home_router.include_router(started.router, prefix="", tags=["started"])
home_router.include_router(queues.router, prefix="", tags=["queues"])
