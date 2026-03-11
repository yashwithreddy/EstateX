import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import cors_origins_list, settings
from app.db.session import Base, engine
from app.ml.service import ml_service
from app.routers import admin, ai, auth, dashboard, investments, predict, properties

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("estatex.api")

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_debug_logger(request: Request, call_next):
    start = time.perf_counter()
    logger.info("REQ %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("ERR %s %s", request.method, request.url.path)
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("RES %s %s status=%s duration_ms=%s", request.method, request.url.path, response.status_code, duration_ms)
    return response


app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(investments.router)
app.include_router(admin.router)
app.include_router(ai.router)
app.include_router(predict.router)
app.include_router(dashboard.router)


@app.get("/")
def health_check():
    return {"service": "EstateX", "status": "ok"}


@app.on_event("startup")
def startup_checks() -> None:
    Base.metadata.create_all(bind=engine)
    model_status = ml_service.preload()
    logger.info("startup complete model_status=%s cors=%s", model_status, cors_origins_list())
