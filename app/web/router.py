from fastapi import APIRouter

from app.web.routes import home

home_router = APIRouter()
home_router.include_router(home.router, tags=["home"])
home_router.include_router(home.router, prefix="", tags=["home"])
