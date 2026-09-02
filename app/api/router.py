from fastapi import APIRouter

from app.api.routers import analytics, auth, compensation, employees, exports, imports

master_router = APIRouter()

master_router.include_router(auth.router)
master_router.include_router(employees.router)
master_router.include_router(compensation.router)
master_router.include_router(analytics.router)
master_router.include_router(exports.router)
master_router.include_router(imports.router)
