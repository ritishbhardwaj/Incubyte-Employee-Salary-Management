from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api.router import master_router
from app.config import get_settings
from app.database.session import REQUIRED_TABLES, get_db
from app.exceptions import AppError
from app.org import ORG_NAME

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

    application.include_router(master_router)
    _mount_frontend(application)
    return application




def _mount_frontend(application: FastAPI) -> None:
    if FRONTEND_DIST.is_dir():
        application.frontend(
            "/",
            directory=str(FRONTEND_DIST),
            fallback="index.html",
            check_dir=False,
        )
        return
    if get_settings().is_production:
        raise RuntimeError(
            f"SPA build missing at {FRONTEND_DIST}. "
            "Run `npm --prefix frontend run build` before deploying."
        )


app = create_app()
