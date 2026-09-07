"""FastAPI application assembly: routers, error mapping, static serving, seed.

The single server exposes the JSON API under ``/api`` and serves the static
customer (``/``) and admin (``/admin``) apps. On startup it creates tables,
seeds the demo store, and binds the event loop for thread-safe SSE publishing.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, customer, stream
from app.core.db import SessionLocal, create_all
from app.core.errors import DomainError
from app.core.events import broker
from app.seed import seed_if_empty

_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_all()
    broker.bind_loop(asyncio.get_running_loop())
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Table Order", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(admin.router)
app.include_router(stream.router)


@app.exception_handler(DomainError)
async def _domain_error_handler(_request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/", include_in_schema=False)
def customer_app():
    index = _FRONTEND / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"detail": "고객 앱이 아직 배포되지 않았습니다."}, status_code=404
    )


@app.get("/admin", include_in_schema=False)
def admin_app():
    index = _FRONTEND / "admin.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"detail": "관리자 앱이 아직 배포되지 않았습니다."}, status_code=404
    )


if (_FRONTEND / "static").is_dir():
    app.mount("/static", StaticFiles(directory=_FRONTEND / "static"), name="static")
