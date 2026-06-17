from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.web.router import home_router
from app.core.config import settings
from app.core.templating import STATIC_DIR
from app.db.init_db import init_db
from app.core.config import settings

import traceback


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.auto_create_tables:
        await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.starlette_session_middleware_secret_key,
    )

    @app.middleware("http")
    async def exception_middleware(request: Request, call_next):
        try:
            return await call_next(request)

        except Exception as exc:
            traceback.print_exc()
            if request.url.path.startswith(settings.api_v1_prefix):
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=500,
                    # content={"detail": f"Internal server error: {str(exc)}"},
                    content=str(exc),
                )

            return HTMLResponse(
                content=settings.custom_error(exc_status_code=500),
                status_code=500,
            )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        return HTMLResponse(
            content=settings.custom_error(exc_status_code=exc.status_code),
            status_code=exc.status_code,
        )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(home_router, prefix="")

    return app


app = create_app()
