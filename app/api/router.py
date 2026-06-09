from fastapi import APIRouter

from app.api.routes import health, users, otp

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(otp.router, prefix="/otp", tags=["otp"])
