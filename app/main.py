from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.db import REQUIRED_TABLES, get_db
from app.core.exceptions import AppError
from app.core.org import ORG_NAME

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    application = FastAPI(
        title="IncubyteESM",
        summary=f"{ORG_NAME} employee salary management for the HR Manager.",
        version="0.1.0",
    )

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/ready")
    def ready(db: Session = Depends(get_db)) -> JSONResponse:
        try:
            db.execute(text("SELECT 1"))
            tables = set(inspect(db.get_bind()).get_table_names())
        except Exception:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "detail": "database unreachable or schema not migrated",
                },
            )
        if not all(name in tables for name in REQUIRED_TABLES):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "detail": "database unreachable or schema not migrated",
                },
            )
        return JSONResponse(status_code=200, content={"status": "ready"})

    _include_routers(application)
    _mount_frontend(application)
    return application


def _include_routers(application: FastAPI) -> None:
    from app.analytics.router import router as analytics_router
    from app.auth.router import router as auth_router
    from app.compensation.router import router as compensation_router
    from app.employees.router import router as employees_router
    from app.exports.router import router as exports_router
    from app.imports.router import router as imports_router

    application.include_router(auth_router)
    application.include_router(employees_router)
    application.include_router(compensation_router)
    application.include_router(analytics_router)
    application.include_router(exports_router)
    application.include_router(imports_router)


def _mount_frontend(application: FastAPI) -> None:
    if not FRONTEND_DIST.exists():
        return
    application.frontend("/", directory=str(FRONTEND_DIST), fallback="index.html")


app = create_app()
