from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://microclimate:changeme@localhost:5432/microclimate_hk"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    
    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://microclimate.hk"
    ]
    
    # Hong Kong Observatory API
    HKO_API_KEY: str = ""
    HKO_BASE_URL: str = "https://data.weather.gov.hk"
    
    # ML Models
    ML_MODEL_PATH: str = "/ml-models/models"
    URBAN_CANYON_MODEL: str = "urban_canyon_v1.h5"
    SENSOR_FUSION_MODEL: str = "sensor_fusion_v1.h5"
    
    # Weather Grid
    GRID_RESOLUTION: int = 100  # meters
    MAX_GRID_SIZE: int = 10000  # max cells per request
    
    # Real-time Updates
    WEBSOCKET_UPDATE_INTERVAL: int = 15  # seconds
    SENSOR_BATCH_SIZE: int = 1000
    
    # Feature Flags
    ENABLE_CROWDSOURCING: bool = True
    ENABLE_ML_PREDICTIONS: bool = True
    ENABLE_OFFLINE_SYNC: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
