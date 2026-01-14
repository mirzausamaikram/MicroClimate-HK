from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.v1 import weather, alerts, sensors, forecasts, ml
from app.core.config import settings
from app.db.database import engine, Base
from app.services.cache import RedisCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting MicroClimate HK API...")
    
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis cache
    await RedisCache.initialize()
    
    logger.info("API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    await RedisCache.close()
    await engine.dispose()
    logger.info("API shutdown complete")


app = FastAPI(
    title="MicroClimate HK API",
    description="Block-by-block weather prediction for Hong Kong",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# API Routes
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(sensors.router, prefix="/api/sensors", tags=["Sensors"])
app.include_router(forecasts.router, prefix="/api/forecasts", tags=["Forecasts"])
app.include_router(ml.router, prefix="/api/ml", tags=["Machine Learning"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
