# MicroClimate HK - API Integration Guide

## Hong Kong Observatory (HKO) API

### Official Data Sources

1. **Current Weather Report API**
   - Endpoint: `https://data.weather.gov.hk/weatherAPI/opendata/weather.php`
   - Parameters: `dataType=rhrread` (Regional Weather)
   - Update Frequency: Every minute
   - Data: Temperature, humidity, rainfall, wind

2. **9-Day Forecast API**
   - Endpoint: `https://data.weather.gov.hk/weatherAPI/opendata/weather.php`
   - Parameters: `dataType=fnd` (9-day forecast)
   - Update Frequency: Daily
   - Data: Daily forecasts, temperature ranges

3. **Warnings and Special Weather Tips**
   - Endpoint: `https://data.weather.gov.hk/weatherAPI/opendata/weather.php`
   - Parameters: `dataType=warnsum`
   - Update Frequency: As issued
   - Data: Typhoon signals, rainstorm warnings, heat/cold warnings

### Implementation

```python
# backend-api/app/integrations/hko_api.py

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HKOClient:
    """Hong Kong Observatory API Client"""
    
    BASE_URL = "https://data.weather.gov.hk/weatherAPI/opendata"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_current_weather(self) -> Dict[str, Any]:
        """Get current regional weather"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/weather.php",
                params={"dataType": "rhrread", "lang": "en"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch HKO weather: {e}")
            return {}
    
    async def get_forecast(self) -> Dict[str, Any]:
        """Get 9-day forecast"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/weather.php",
                params={"dataType": "fnd", "lang": "en"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch HKO forecast: {e}")
            return {}
    
    async def get_warnings(self) -> Dict[str, Any]:
        """Get active weather warnings"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/weather.php",
                params={"dataType": "warnsum", "lang": "en"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch HKO warnings: {e}")
            return {}
    
    async def close(self):
        await self.client.aclose()


# Usage in service
async def sync_hko_data():
    """Sync data from HKO API"""
    hko_client = HKOClient()
    
    try:
        # Get current weather from all HKO stations
        current = await hko_client.get_current_weather()
        
        # Process and store readings
        if "temperature" in current and "data" in current["temperature"]:
            for station in current["temperature"]["data"]:
                # Store official reading in database
                await store_official_reading(
                    station_id=station["place"],
                    temperature=station["value"],
                    timestamp=datetime.fromisoformat(current["updateTime"])
                )
        
        # Get warnings
        warnings = await hko_client.get_warnings()
        if warnings:
            await process_warnings(warnings)
    
    finally:
        await hko_client.close()
```

## Hong Kong Lands Department - 3D Spatial Data

### Data Sources

1. **3D Digital Topographic Map**
   - Source: data.gov.hk
   - Format: GeoJSON, SHP
   - Data: Building footprints, heights, terrain elevation

2. **Building Height Information**
   - Source: Lands Department
   - Format: CSV, Database
   - Data: Address, height, floors, coordinates

### Implementation

```python
# backend-api/app/integrations/lands_dept.py

import geopandas as gpd
from shapely.geometry import Point, Polygon
from typing import List, Dict
import httpx


async def fetch_building_data(bounds: Dict[str, float]) -> gpd.GeoDataFrame:
    """
    Fetch building data from Lands Department
    
    In production, this would query the official API or dataset.
    For now, uses cached/downloaded data.
    """
    
    # Load from local GeoJSON (downloaded from data.gov.hk)
    buildings = gpd.read_file("data/hk_buildings.geojson")
    
    # Filter to bounding box
    buildings = buildings.cx[
        bounds["min_lng"]:bounds["max_lng"],
        bounds["min_lat"]:bounds["max_lat"]
    ]
    
    return buildings


async def get_building_shadows(
    location: Point,
    time: datetime,
    buildings: gpd.GeoDataFrame
) -> List[Dict]:
    """
    Calculate building shadows affecting a location
    
    Uses sun position and building heights to determine
    which buildings cast shadows on the target location.
    """
    
    from pysolar.solar import get_azimuth, get_altitude
    
    # Calculate sun position
    altitude = get_altitude(location.y, location.x, time)
    azimuth = get_azimuth(location.y, location.x, time)
    
    # Find buildings that cast shadows
    shadows = []
    for idx, building in buildings.iterrows():
        # Simplified shadow calculation
        # In production, use full 3D ray tracing
        distance = location.distance(building.geometry.centroid)
        height = building.get("height_meters", 0)
        
        # Shadow length based on sun altitude
        if altitude > 0:
            shadow_length = height / np.tan(np.radians(altitude))
            
            if distance < shadow_length:
                shadows.append({
                    "building_id": building.get("building_id"),
                    "height": height,
                    "distance": distance,
                    "blocks_sun": True
                })
    
    return shadows
```

## Real-time Updates Integration

```python
# backend-api/app/services/sync_service.py

import asyncio
from datetime import datetime
from app.integrations.hko_api import HKOClient
from app.services.cache import RedisCache


class WeatherSyncService:
    """Service to continuously sync weather data"""
    
    def __init__(self):
        self.hko_client = HKOClient()
        self.running = False
    
    async def start(self):
        """Start continuous sync"""
        self.running = True
        
        # Run sync tasks
        await asyncio.gather(
            self.sync_official_data(),
            self.aggregate_crowdsourced_data(),
            self.update_forecasts()
        )
    
    async def sync_official_data(self):
        """Sync HKO data every minute"""
        while self.running:
            try:
                data = await self.hko_client.get_current_weather()
                await self.process_and_store(data)
                
                # Publish to Redis for real-time updates
                await RedisCache.publish("weather:updates", data)
                
            except Exception as e:
                logger.error(f"Sync error: {e}")
            
            await asyncio.sleep(60)  # Every minute
    
    async def aggregate_crowdsourced_data(self):
        """Aggregate sensor readings every 15 seconds"""
        while self.running:
            # Aggregate recent crowdsourced readings
            # Update weather grid
            # Publish to WebSocket clients
            await asyncio.sleep(15)
    
    async def update_forecasts(self):
        """Update ML forecasts every hour"""
        while self.running:
            # Run ML models to generate predictions
            await asyncio.sleep(3600)  # Every hour
```

## Integration with Frontend

```typescript
// frontend/src/lib/api/hkoData.ts

export interface HKOWeatherData {
  temperature: number;
  humidity: number;
  rainfall: number;
  updateTime: string;
}

export async function fetchHKOData(): Promise<HKOWeatherData> {
  const response = await fetch(
    `${import.meta.env.PUBLIC_API_URL}/api/hko/current`
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch HKO data');
  }
  
  return response.json();
}
```

## Data Attribution

Always attribute data sources as required:

```html
<!-- In frontend -->
<div class="attribution">
  Weather data provided by Hong Kong Observatory
  <br/>
  Building data © Lands Department, HKSAR Government
</div>
```

## Rate Limiting

Respect API rate limits:

```python
# Implement rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/hko/current")
@limiter.limit("60/minute")  # Max 60 requests per minute
async def get_hko_current(request: Request):
    # ...
```
