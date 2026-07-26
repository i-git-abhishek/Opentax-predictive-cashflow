import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter

from app.core.database import Base, engine
from app.jobs.scheduler import start_scheduler, shutdown_scheduler
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints import ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized.")
    start_scheduler()
    yield
    logger.info("Application shutting down...")
    shutdown_scheduler()


app = FastAPI(
    title="OpenTax Predictive Cashflow API",
    version="1.0.0",
    description="Unified ingestion, calculation, and alerting service.",
    lifespan=lifespan,
)

app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(alerts_router)
app.include_router(api_v1_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "OpenTax Predictive Cashflow API", "version": "1.0.0"}