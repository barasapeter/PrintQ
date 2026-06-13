from fastapi import APIRouter

from app.api.routes import health, otp, users, vendors, shops, workorders

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(otp.router, prefix="/otp", tags=["otp"])
api_router.include_router(vendors.router, prefix="/vendor", tags=["vendor"])
api_router.include_router(shops.router, prefix="/shop", tags=["shop"])
api_router.include_router(workorders.router, prefix="/workorder", tags=["workorder"])
