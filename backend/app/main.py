import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter

from app.core.database import engine, Base
from app.jobs.scheduler import start_scheduler, shutdown_scheduler
from app.api.v1.endpoints.alerts import router as alerts_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Application starting up...")
    
    # Auto-create SQLite database tables (Team 2 schema configuration requirement)
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized.")

    # Start the background task scheduler
    logger.info("Starting background task scheduler...")
    start_scheduler()
    
    yield
    
    # Shutdown actions
    logger.info("Application shutting down...")
    logger.info("Shutting down background task scheduler...")
    shutdown_scheduler()

# Initialize FastAPI with lifespan handlers
app = FastAPI(
    title="OpenTax Predictive Cashflow - Alerts & Ingestion Core",
    version="1.0.0",
    description="Team 3 background scheduler and notification services engine with integrated data feeds.",
    lifespan=lifespan
)

# Route registration
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(alerts_router)

app.include_router(api_v1_router)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "OpenTax Messaging & Scheduling Control Plane",
        "version": "1.0.0"
    }
