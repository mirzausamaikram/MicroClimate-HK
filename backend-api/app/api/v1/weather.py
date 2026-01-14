from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.functions import ST_Distance, ST_MakePoint, ST_SetSRID
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import WeatherReading
from app.schemas.weather import (
    WeatherResponse, 
    WeatherGridRequest, 
    WeatherGridResponse,
    VerticalProfileResponse
)
from app.services.weather_service import WeatherService
from app.services.cache import RedisCache

router = APIRouter()


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    elevation: Optional[float] = Query(None, ge=0, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current weather for a specific location
    
    - **lat**: Latitude (required)
    - **lng**: Longitude (required)
    - **elevation**: Elevation in meters (optional, for floor-level predictions)
    """
    
    # Check cache first
    cache_key = f"weather:current:{lat}:{lng}:{elevation or 0}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached
    
    # Get weather service
    weather_service = WeatherService(db)
    
    # Fetch current weather
    weather = await weather_service.get_current_weather(lat, lng, elevation)
    
    if not weather:
        raise HTTPException(status_code=404, detail="No weather data available for this location")
    
    # Cache the result
    await RedisCache.set(cache_key, weather, ttl=300)  # 5 minutes
    
    return weather


@router.post("/grid", response_model=WeatherGridResponse)
async def get_weather_grid(
    request: WeatherGridRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get weather grid for a bounding box
    
    Returns a 3D weather mesh with data for each grid cell
    """
    
    weather_service = WeatherService(db)
    grid = await weather_service.generate_weather_grid(
        request.bounds,
        request.resolution
    )
    
    return grid


@router.get("/vertical", response_model=VerticalProfileResponse)
async def get_vertical_profile(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    max_floor: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Get vertical weather profile for a location
    
    Returns weather conditions at different elevation levels
    """
    
    weather_service = WeatherService(db)
    profile = await weather_service.get_vertical_profile(lat, lng, max_floor)
    
    return profile


@router.get("/history")
async def get_weather_history(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical weather data for a location
    
    - **hours**: Number of hours to look back (max 168 = 7 days)
    """
    
    # Query historical data
    since = datetime.utcnow() - timedelta(hours=hours)
    point = ST_SetSRID(ST_MakePoint(lng, lat, 0), 4326)
    
    stmt = select(WeatherReading).where(
        and_(
            WeatherReading.timestamp >= since,
            ST_Distance(WeatherReading.location, point) < 1000  # Within 1km
        )
    ).order_by(WeatherReading.timestamp.desc()).limit(1000)
    
    result = await db.execute(stmt)
    readings = result.scalars().all()
    
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "humidity": r.humidity,
            "rainfall": r.rainfall,
            "wind_speed": r.wind_speed
        }
        for r in readings
    ]


@router.get("/laundry-index")
async def get_laundry_index(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    elevation: Optional[float] = Query(None),
    facing: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get laundry dry index for a specific location
    
    Predicts how long it will take to dry laundry based on:
    - Temperature
    - Humidity
    - Sunlight exposure
    - Wind speed
    - Building shadows
    """
    
    weather_service = WeatherService(db)
    laundry_data = await weather_service.calculate_laundry_index(
        lat, lng, elevation, facing
    )
    
    return laundry_data


@router.get("/mould-risk")
async def get_mould_risk(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    elevation: Optional[float] = Query(None),
    facing: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mould risk score for a location
    
    Calculates risk based on:
    - Humidity levels
    - Temperature
    - Ventilation (wind)
    - Sunlight exposure
    """
    
    weather_service = WeatherService(db)
    mould_risk = await weather_service.calculate_mould_risk(
        lat, lng, elevation, facing
    )
    
    return mould_risk
