from fastapi import APIRouter

from app.api.routes import admin, auth, generation


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(generation.router)
api_router.include_router(admin.router)
