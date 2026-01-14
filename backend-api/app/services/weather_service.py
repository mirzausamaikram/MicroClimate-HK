from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.functions import ST_Distance, ST_MakePoint, ST_SetSRID, ST_Z
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import griddata

from app.db.models import WeatherReading, SensorStation, BuildingData
from app.schemas.weather import (
    WeatherResponse, 
    Coordinates, 
    WeatherGridResponse, 
    GridCell,
    GridBounds,
    VerticalProfileResponse,
    WeatherLayer
)
from app.services.ml_service import MLService


class WeatherService:
    """Service for weather data operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ml_service = MLService()
    
    async def get_current_weather(
        self, 
        lat: float, 
        lng: float, 
        elevation: Optional[float] = None
    ) -> Optional[WeatherResponse]:
        """Get current weather for a location"""
        
        # Create point geometry
        elev = elevation or 0
        point = ST_SetSRID(ST_MakePoint(lng, lat, elev), 4326)
        
        # Find nearest weather reading (within last 30 minutes)
        since = datetime.utcnow() - timedelta(minutes=30)
        
        stmt = select(WeatherReading).where(
            and_(
                WeatherReading.timestamp >= since,
                ST_Distance(WeatherReading.location, point) < 5000  # Within 5km
            )
        ).order_by(
            ST_Distance(WeatherReading.location, point)
        ).limit(10)
        
        result = await self.db.execute(stmt)
        readings = result.scalars().all()
        
        if not readings:
            return None
        
        # Use ML model to interpolate/predict for exact location
        if len(readings) >= 3:
            weather_data = await self.ml_service.interpolate_weather(
                readings, lat, lng, elev
            )
        else:
            # Use nearest reading
            reading = readings[0]
            weather_data = {
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "rainfall": reading.rainfall,
                "wind_speed": reading.wind_speed,
                "wind_direction": reading.wind_direction,
                "pressure": reading.pressure,
                "uv_index": reading.uv_index
            }
        
        return WeatherResponse(
            location=Coordinates(
                latitude=lat,
                longitude=lng,
                elevation=elev
            ),
            timestamp=datetime.utcnow(),
            elevation=elev,
            **weather_data
        )
    
    async def generate_weather_grid(
        self,
        bounds: GridBounds,
        resolution: int = 100
    ) -> WeatherGridResponse:
        """Generate weather grid for a bounding box"""
        
        # Calculate grid points
        lat_points = np.arange(bounds.min_lat, bounds.max_lat, resolution / 111000)  # ~111km per degree
        lng_points = np.arange(bounds.min_lng, bounds.max_lng, resolution / (111000 * np.cos(np.radians(bounds.min_lat))))
        
        grid_cells: List[GridCell] = []
        
        # Fetch all readings in the area
        since = datetime.utcnow() - timedelta(minutes=30)
        
        bbox = f"POLYGON(({bounds.min_lng} {bounds.min_lat}, {bounds.max_lng} {bounds.min_lat}, {bounds.max_lng} {bounds.max_lat}, {bounds.min_lng} {bounds.max_lat}, {bounds.min_lng} {bounds.min_lat}))"
        
        stmt = select(WeatherReading).where(
            and_(
                WeatherReading.timestamp >= since,
                WeatherReading.location.ST_Within(ST_SetSRID(ST_GeomFromText(bbox), 4326))
            )
        )
        
        result = await self.db.execute(stmt)
        readings = result.scalars().all()
        
        if readings:
            # Interpolate weather data across grid
            points = np.array([[r.location.x, r.location.y] for r in readings])
            temps = np.array([r.temperature for r in readings])
            humidity_vals = np.array([r.humidity for r in readings])
            
            for lat in lat_points[:20]:  # Limit for demo
                for lng in lng_points[:20]:
                    # Interpolate values
                    temp = griddata(points, temps, (lng, lat), method='linear')
                    humid = griddata(points, humidity_vals, (lng, lat), method='linear')
                    
                    if not np.isnan(temp):
                        weather = WeatherResponse(
                            location=Coordinates(latitude=lat, longitude=lng, elevation=0),
                            timestamp=datetime.utcnow(),
                            temperature=float(temp),
                            humidity=float(humid),
                            rainfall=0.0,
                            wind_speed=0.0,
                            elevation=0.0
                        )
                        
                        grid_cells.append(GridCell(
                            coordinates=Coordinates(latitude=lat, longitude=lng),
                            weather=weather,
                            confidence=0.8,
                            source="interpolated"
                        ))
        
        return WeatherGridResponse(
            bounds=bounds,
            resolution=resolution,
            data=grid_cells
        )
    
    async def get_vertical_profile(
        self,
        lat: float,
        lng: float,
        max_floor: int = 100
    ) -> VerticalProfileResponse:
        """Get vertical weather profile"""
        
        layers: List[WeatherLayer] = []
        
        # Get base weather
        base_weather = await self.get_current_weather(lat, lng, 0)
        
        if not base_weather:
            return VerticalProfileResponse(
                location=Coordinates(latitude=lat, longitude=lng),
                timestamp=datetime.utcnow(),
                layers=[]
            )
        
        # Calculate vertical gradient (simplified model)
        # Real implementation would use atmospheric models
        floor_ranges = [(1, 10), (11, 20), (21, 40), (41, 60), (61, 100)]
        
        for floor_min, floor_max in floor_ranges:
            if floor_max <= max_floor:
                elevation = floor_max * 3  # ~3m per floor
                
                # Temperature decreases ~0.6°C per 100m
                temp_offset = -(elevation / 100) * 0.6
                
                # Humidity slightly decreases with elevation
                humid_offset = -(elevation / 100) * 2
                
                layers.append(WeatherLayer(
                    elevation_range=(floor_min, floor_max),
                    temperature=base_weather.temperature + temp_offset,
                    humidity=max(0, min(100, base_weather.humidity + humid_offset)),
                    visibility=10000,  # meters
                    rainfall=base_weather.rainfall,
                    wind_speed=base_weather.wind_speed * (1 + elevation / 500)  # Wind increases with height
                ))
        
        return VerticalProfileResponse(
            location=Coordinates(latitude=lat, longitude=lng),
            timestamp=datetime.utcnow(),
            layers=layers
        )
    
    async def calculate_laundry_index(
        self,
        lat: float,
        lng: float,
        elevation: Optional[float] = None,
        facing: Optional[str] = None
    ) -> Dict:
        """Calculate laundry dry index"""
        
        weather = await self.get_current_weather(lat, lng, elevation)
        
        if not weather:
            return {"error": "No weather data available"}
        
        # Simple laundry index calculation
        # Real implementation would use ML model
        
        # Base dry time calculation
        temp_factor = max(0, (weather.temperature - 15) / 20)  # 0 to 1
        humid_factor = 1 - (weather.humidity / 100)
        wind_factor = min(1, weather.wind_speed / 20)
        
        # Combined factor
        dry_factor = (temp_factor * 0.4 + humid_factor * 0.4 + wind_factor * 0.2)
        
        # Dry time in minutes (base 180 minutes in poor conditions)
        dry_time = int(180 * (1 - dry_factor))
        
        # Recommendation
        if dry_time < 60:
            recommendation = "excellent"
        elif dry_time < 120:
            recommendation = "good"
        elif dry_time < 180:
            recommendation = "fair"
        elif dry_time < 300:
            recommendation = "poor"
        else:
            recommendation = "avoid"
        
        return {
            "location": {"latitude": lat, "longitude": lng},
            "timestamp": datetime.utcnow().isoformat(),
            "dry_time_minutes": dry_time,
            "recommendation": recommendation,
            "factors": {
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "wind_speed": weather.wind_speed
            }
        }
    
    async def calculate_mould_risk(
        self,
        lat: float,
        lng: float,
        elevation: Optional[float] = None,
        facing: Optional[str] = None
    ) -> Dict:
        """Calculate mould risk score"""
        
        weather = await self.get_current_weather(lat, lng, elevation)
        
        if not weather:
            return {"error": "No weather data available"}
        
        # Mould risk factors
        humid_risk = (weather.humidity - 60) / 40 if weather.humidity > 60 else 0
        temp_risk = 1 if 20 <= weather.temperature <= 30 else 0.5
        ventilation_factor = 1 - min(1, weather.wind_speed / 10)
        
        # Combined mould risk (0-100)
        mould_risk = int((humid_risk * 0.5 + temp_risk * 0.3 + ventilation_factor * 0.2) * 100)
        
        return {
            "location": {"latitude": lat, "longitude": lng},
            "timestamp": datetime.utcnow().isoformat(),
            "mould_risk_score": min(100, max(0, mould_risk)),
            "risk_level": "high" if mould_risk > 70 else "medium" if mould_risk > 40 else "low",
            "factors": {
                "humidity": weather.humidity,
                "temperature": weather.temperature,
                "ventilation": weather.wind_speed
            }
        }
