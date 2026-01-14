"""
Mock MicroClimate API Server for Demo
Provides sample weather data for visualization
"""

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import math
import random
import json
from typing import Dict, Optional
import hashlib
try:
    from ephem import next_full_moon, previous_full_moon, Moon, Observer
    EPHEM_AVAILABLE = True
except ImportError:
    EPHEM_AVAILABLE = False
    next_full_moon = previous_full_moon = Moon = Observer = None

app = FastAPI(
    title="MicroClimate HK API",
    description="Hyperlocal weather prediction for Hong Kong",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for Hong Kong
HONG_KONG_CENTER = {
    "lat": 22.3193,
    "lon": 114.1694,
}

# Cache for weather data (simple in-memory cache)
WEATHER_CACHE: Dict[str, tuple] = {}
CACHE_DURATION = 300  # 5 minutes in seconds

# Popular locations in Hong Kong
LOCATIONS = {
    "central": {"lat": 22.2855, "lon": 114.1577, "name": "Central, Hong Kong Island"},
    "mong-kok": {"lat": 22.3193, "lon": 114.1694, "name": "Mong Kok, Kowloon"},
    "shatin": {"lat": 22.3870, "lon": 114.1857, "name": "Sha Tin, New Territories"},
    "tuen-mun": {"lat": 22.3830, "lon": 113.9755, "name": "Tuen Mun, New Territories"},
    "sai-kung": {"lat": 22.3129, "lon": 114.2668, "name": "Sai Kung, New Territories"},
    "causeway": {"lat": 22.3047, "lon": 114.0181, "name": "Causeway Bay, Hong Kong Island"},
    "tsim-sha-tsui": {"lat": 22.2969, "lon": 114.1738, "name": "Tsim Sha Tsui, Kowloon"},
    "victoria-peak": {"lat": 22.3165, "lon": 114.1526, "name": "Victoria Peak"},
}

def get_cache_key(lat: float, lon: float, elevation: float) -> str:
    """Generate cache key for weather data"""
    return hashlib.md5(f"{lat:.4f},{lon:.4f},{elevation}".encode()).hexdigest()

def calculate_aqi(pm25: float) -> dict:
    """Calculate Air Quality Index from PM2.5"""
    # AQI scale based on PM2.5 concentration (μg/m³)
    if pm25 <= 12:
        aqi = (pm25 / 12) * 50
        category = "Good"
        color = "#00E400"
    elif pm25 <= 35.4:
        aqi = 50 + ((pm25 - 12) / 23.4) * 50
        category = "Moderate"
        color = "#FFFF00"
    elif pm25 <= 55.4:
        aqi = 100 + ((pm25 - 35.4) / 20) * 50
        category = "Unhealthy for Sensitive Groups"
        color = "#FF7E00"
    elif pm25 <= 150.4:
        aqi = 150 + ((pm25 - 55.4) / 95) * 50
        category = "Unhealthy"
        color = "#FF0000"
    else:
        aqi = 200 + ((pm25 - 150.4) / 50) * 100
        category = "Very Unhealthy"
        color = "#8F3F97"
    
    return {
        "value": round(min(500, aqi), 0),
        "category": category,
        "color": color
    }

def calculate_heat_index(temp_c: float, humidity: float) -> float:
    """Calculate heat index using temperature in Celsius and humidity percentage"""
    # Convert to Fahrenheit for calculation
    temp_f = (temp_c * 9/5) + 32
    
    # Heat index formula
    c1 = -42.379
    c2 = 2.04901523
    c3 = 10.14333127
    c4 = -0.22475541
    c5 = -0.00683783
    c6 = -0.05481717
    c7 = 0.00122874
    c8 = 0.00085282
    c9 = -0.00000199
    
    hi = (c1 + c2*temp_f + c3*humidity + c4*temp_f*humidity + 
          c5*temp_f*temp_f + c6*humidity*humidity + 
          c7*temp_f*temp_f*humidity + c8*temp_f*humidity*humidity + 
          c9*temp_f*temp_f*humidity*humidity)
    
    # Convert back to Celsius
    return round((hi - 32) * 5/9, 1)

def calculate_wind_chill(temp_c: float, wind_speed: float) -> float:
    """Calculate wind chill using temperature in Celsius and wind speed in m/s"""
    # Convert m/s to km/h
    wind_kmh = wind_speed * 3.6
    
    # Wind chill formula (only applies when temp < 10°C)
    if temp_c < 10:
        wc = 13.12 + 0.6215*temp_c - 11.37*(wind_kmh**0.16) + 0.3965*(temp_c)*(wind_kmh**0.16)
        return round(wc, 1)
    return round(temp_c, 1)

def calculate_comfort_index(temp_c: float, humidity: float) -> dict:
    """Calculate humidity comfort index (discomfort index)"""
    # Discomfort Index (DI) = temp + 0.5 * humidity
    di = temp_c + (0.5 * humidity)
    
    if di < 20:
        level = "Comfortable"
        emoji = "😊"
    elif di < 25:
        level = "Fairly Comfortable"
        emoji = "🙂"
    elif di < 30:
        level = "Uncomfortably Warm"
        emoji = "😅"
    elif di < 35:
        level = "Very Uncomfortable"
        emoji = "😰"
    else:
        level = "Dangerously Hot"
        emoji = "🥵"
    
    return {
        "index": round(di, 1),
        "level": level,
        "emoji": emoji
    }

def get_sunrise_sunset(lat: float, lon: float):
    """Calculate sunrise and sunset times for a location"""
    """Calculate sunrise and sunset times with graceful fallback when ephem is unavailable"""
    if not EPHEM_AVAILABLE:
        sunrise = datetime.utcnow().replace(hour=6, minute=30, second=0, microsecond=0)
        sunset = datetime.utcnow().replace(hour=18, minute=30, second=0, microsecond=0)
        return {
            "sunrise_time": sunrise.strftime("%H:%M"),
            "sunset_time": sunset.strftime("%H:%M"),
            "day_length": "12:00:00",
            "method": "fallback",
        }

    try:
        obs = Observer()
        obs.lat = str(lat)
        obs.lon = str(lon)
        obs.elevation = 50
        obs.date = datetime.utcnow()
        obs.pressure = 0
        obs.horizon = '-0:34'
        sunrise = obs.next_rising(next_full_moon(obs.date)).datetime()
        sunset = obs.next_setting(next_full_moon(obs.date)).datetime()
        return {
            "sunrise_time": sunrise.strftime("%H:%M"),
            "sunset_time": sunset.strftime("%H:%M"),
            "day_length": str(sunset - sunrise),
            "method": "ephem",
        }
    except Exception:
        sunrise = datetime.utcnow().replace(hour=6, minute=30, second=0, microsecond=0)
        sunset = datetime.utcnow().replace(hour=18, minute=30, second=0, microsecond=0)
        return {
            "sunrise_time": sunrise.strftime("%H:%M"),
            "sunset_time": sunset.strftime("%H:%M"),
            "day_length": "12:00:00",
            "method": "fallback",
        }

def get_moon_phase():
    """Get current moon phase"""
    """Calculate moon phase and illumination with optional ephem support"""
    if not EPHEM_AVAILABLE:
        return {
            "phase": "Waxing Gibbous",
            "illumination": 75.0,
            "emoji": "🌔",
            "percentage": 75,
            "method": "fallback",
        }

    try:
        moon = Moon()
        moon.compute()
        phase = moon.phase / 100
        if phase < 0.03:
            moon_name = "New Moon"
            emoji = "🌑"
        elif phase < 0.25:
            moon_name = "Waxing Crescent"
            emoji = "🌒"
        elif phase < 0.5:
            moon_name = "First Quarter"
            emoji = "🌓"
        elif phase < 0.75:
            moon_name = "Waxing Gibbous"
            emoji = "🌔"
        else:
            moon_name = "Full Moon"
            emoji = "🌕"

        phase_pct = round((1 - phase) * 100) if phase > 0.5 else round(phase * 100)

        return {
            "phase": moon_name,
            "illumination": round(moon.phase, 1),
            "emoji": emoji,
            "percentage": phase_pct,
            "method": "ephem",
        }
    except Exception:
        return {
            "phase": "Waxing Gibbous",
            "illumination": 75.0,
            "emoji": "🌔",
            "percentage": 75,
            "method": "fallback",
        }

def get_wind_direction_name(degrees: int) -> str:
    """Convert wind direction degrees to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return directions[idx]

def generate_weather_at_location(lat: float, lon: float, elevation: float = 50, use_cache: bool = True) -> dict:
    """Generate mock weather data for a location based on distance and elevation"""
    
    cache_key = get_cache_key(lat, lon, elevation)
    
    # Check cache
    if use_cache and cache_key in WEATHER_CACHE:
        cached_data, cached_time = WEATHER_CACHE[cache_key]
        if (datetime.utcnow() - cached_time).total_seconds() < CACHE_DURATION:
            return cached_data
    
    # Base weather
    base_temp = 24.0 + random.uniform(-2, 2)
    base_humidity = 70.0 + random.uniform(-10, 10)
    
    # Elevation effect (~0.6°C per 100m)
    elevation_effect = -(elevation / 100) * 0.6
    
    # Distance from center effect (urban heat island)
    dist = math.sqrt((lat - HONG_KONG_CENTER["lat"])**2 + (lon - HONG_KONG_CENTER["lon"])**2)
    distance_effect = dist * 2  # Cooler farther from downtown
    
    temperature = base_temp + elevation_effect + distance_effect
    humidity = base_humidity - (elevation / 100) * 2  # Lower humidity at higher elevations
    pm25 = 35 + random.uniform(-10, 15)
    
    data = {
        "temperature": round(temperature, 1),
        "humidity": round(max(20, min(100, humidity)), 1),
        "pressure": round(1013.25 - (elevation / 100) * 0.1, 2),
        "wind_speed": round(5 + (elevation / 100) * 0.5 + random.uniform(0, 2), 1),
        "wind_direction": random.randint(0, 360),
        "rainfall": round(random.uniform(0, 5), 1),
        "uv_index": random.randint(3, 9),
        "pm25": round(pm25, 1),
        "aqi": calculate_aqi(pm25),
    }
    
    # Cache the data
    if use_cache:
        WEATHER_CACHE[cache_key] = (data, datetime.utcnow())
    
    return data

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "status": "running",
        "message": "MicroClimate HK API (Demo Mode)",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/v1/weather/current")
async def get_current_weather(
    lat: float = Query(22.3193, description="Latitude"),
    lon: float = Query(114.1694, description="Longitude"),
    elevation: float = Query(50, description="Elevation in meters")
):
    """Get current weather at a specific location"""
    weather = generate_weather_at_location(lat, lon, elevation)
    
    return {
        "location": {
            "latitude": lat,
            "longitude": lon,
            "elevation": elevation,
        },
        "weather": weather,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "demo",
    }

@app.get("/api/v1/weather/grid")
async def get_weather_grid(
    bounds: str = Query("22.2,114.1,22.4,114.3", description="Bounds as min_lat,min_lon,max_lat,max_lon")
):
    """Get weather grid for map visualization"""
    try:
        parts = bounds.split(",")
        min_lat, min_lon, max_lat, max_lon = map(float, parts)
    except:
        min_lat, min_lon, max_lat, max_lon = 22.2, 114.1, 22.4, 114.3
    
    grid_points = []
    step = 0.05
    
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            weather = generate_weather_at_location(lat, lon, 50)
            grid_points.append({
                "lat": lat,
                "lon": lon,
                "temperature": weather["temperature"],
                "humidity": weather["humidity"],
                "wind_speed": weather["wind_speed"],
            })
            lon += step
        lat += step
    
    return {
        "grid_points": grid_points,
        "bounds": {
            "min_lat": min_lat,
            "min_lon": min_lon,
            "max_lat": max_lat,
            "max_lon": max_lon,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/weather/vertical")
async def get_vertical_profile(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
    max_elevation: float = Query(500, description="Maximum elevation in meters")
):
    """Get vertical weather profile by elevation"""
    profile = []
    
    for floor in range(0, int(max_elevation), 50):
        elevation = floor * 5  # Rough conversion: floor to meters
        weather = generate_weather_at_location(lat, lon, elevation)
        profile.append({
            "floor": floor,
            "elevation": elevation,
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "pressure": weather["pressure"],
            "wind_speed": weather["wind_speed"],
        })
    
    return {
        "location": {"lat": lat, "lon": lon},
        "profile": profile,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/weather/laundry-index")
async def get_laundry_index(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
):
    """Get laundry suitability score"""
    weather = generate_weather_at_location(lat, lon, 50)
    
    # Calculate laundry score (0-100)
    temp_score = (weather["temperature"] / 35) * 40  # 0-40
    humidity_score = (100 - weather["humidity"]) / 100 * 30  # 0-30 (lower humidity is better)
    wind_score = min(weather["wind_speed"] / 15 * 30, 30)  # 0-30
    
    total_score = min(100, temp_score + humidity_score + wind_score)
    
    recommendations = []
    if weather["humidity"] > 80:
        recommendations.append("High humidity - clothes may take longer to dry")
    if weather["wind_speed"] < 3:
        recommendations.append("Low wind - consider hanging indoors")
    if weather["temperature"] < 18:
        recommendations.append("Cool weather - drying will be slower")
    if weather["rainfall"] > 2:
        recommendations.append("Rain expected - bring laundry indoors!")
    
    if not recommendations:
        recommendations.append("Perfect conditions for hanging laundry!")
    
    return {
        "score": round(total_score, 1),
        "rating": ["Poor", "Fair", "Good", "Excellent"][int(total_score / 25)],
        "drying_time_hours": round(24 if total_score < 40 else 12 if total_score < 60 else 6 if total_score < 80 else 3, 1),
        "recommendations": recommendations,
        "weather": weather,
    }

@app.get("/api/v1/weather/mould-risk")
async def get_mould_risk(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
):
    """Get mould growth risk assessment"""
    weather = generate_weather_at_location(lat, lon, 50)
    
    # Mould thrives with high humidity (>70%) and moderate temperature (15-30°C)
    humidity_factor = max(0, (weather["humidity"] - 70) / 30)
    temp_factor = 1 if 15 <= weather["temperature"] <= 30 else 0
    
    risk_score = (humidity_factor + temp_factor) * 50
    
    return {
        "risk_score": round(min(100, risk_score), 1),
        "risk_level": ["Low", "Moderate", "High", "Very High"][min(3, int(risk_score / 25))],
        "recommendations": [
            "Ensure good ventilation" if weather["humidity"] > 75 else "Humidity is acceptable",
            "Use dehumidifier if available" if weather["humidity"] > 80 else "Keep windows open",
        ],
        "weather": weather,
    }

@app.get("/api/v1/forecasts/hourly")
async def get_hourly_forecast(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
    hours: int = Query(48, le=168)
):
    """Get hourly forecast for next N hours"""
    forecast = []
    base_temp = generate_weather_at_location(lat, lon, 50)["temperature"]
    
    for i in range(hours):
        hour_offset = i
        # Simulate daily temperature variation
        hour_cycle = (hour_offset % 24) / 24 * 2 * math.pi
        temp_variation = math.sin(hour_cycle) * 3
        
        forecast.append({
            "hour": i,
            "timestamp": (datetime.utcnow() + timedelta(hours=i)).isoformat() + "Z",
            "temperature": round(base_temp + temp_variation + random.uniform(-1, 1), 1),
            "humidity": round(70 + random.uniform(-10, 10), 1),
            "rainfall_probability": round(random.uniform(0, 50), 1),
            "wind_speed": round(5 + random.uniform(-2, 2), 1),
        })
    
    return {
        "location": {"lat": lat, "lon": lon},
        "forecast": forecast,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/alerts/active")
async def get_active_alerts():
    """Get active weather alerts for Hong Kong"""
    alerts = [
        {
            "id": "alert-001",
            "type": "rain",
            "severity": "moderate",
            "message": "Light to moderate rain expected",
            "affected_areas": ["Hong Kong Island", "Kowloon"],
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(hours=3)).isoformat() + "Z",
        }
    ]
    
    # Randomly include additional alerts
    if random.random() > 0.6:
        alerts.append({
            "id": "alert-002",
            "type": "wind",
            "severity": "low",
            "message": "Strong winds on high ground and over the sea",
            "affected_areas": ["Victoria Peak", "High Rise Buildings"],
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(hours=6)).isoformat() + "Z",
        })
    
    if random.random() > 0.7:
        alerts.append({
            "id": "alert-003",
            "type": "uv",
            "severity": "high",
            "message": "High UV index - wear sunscreen",
            "affected_areas": ["All areas"],
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(hours=8)).isoformat() + "Z",
        })
    
    return {
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/locations/search")
async def search_locations(query: str = Query("", description="Location search query")):
    """Search for locations in Hong Kong"""
    results = []
    query_lower = query.lower()
    
    for key, location in LOCATIONS.items():
        if query_lower in key or query_lower in location["name"].lower():
            results.append({
                "id": key,
                "name": location["name"],
                "latitude": location["lat"],
                "longitude": location["lon"],
            })
    
    # If no results, return all locations
    if not results and not query:
        results = [
            {
                "id": key,
                "name": location["name"],
                "latitude": location["lat"],
                "longitude": location["lon"],
            }
            for key, location in LOCATIONS.items()
        ]
    
    return {
        "results": results,
        "total": len(results),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/locations/{location_id}")
async def get_location(location_id: str):
    """Get location details by ID"""
    if location_id in LOCATIONS:
        loc = LOCATIONS[location_id]
        return {
            "id": location_id,
            "name": loc["name"],
            "latitude": loc["lat"],
            "longitude": loc["lon"],
        }
    return {"error": "Location not found"}, 404

@app.get("/api/v1/weather/detailed")
async def get_detailed_weather(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
):
    """Get detailed weather with all calculated indices"""
    weather = generate_weather_at_location(lat, lon, 50)
    sunrise_sunset = get_sunrise_sunset(lat, lon)
    moon = get_moon_phase()
    
    heat_index = calculate_heat_index(weather["temperature"], weather["humidity"])
    wind_chill = calculate_wind_chill(weather["temperature"], weather["wind_speed"])
    comfort_index = calculate_comfort_index(weather["temperature"], weather["humidity"])
    wind_direction = get_wind_direction_name(weather["wind_direction"])
    
    return {
        "location": {"lat": lat, "lon": lon},
        "weather": weather,
        "heat_index": heat_index,
        "wind_chill": wind_chill,
        "comfort_index": comfort_index,
        "wind_direction": {
            "degrees": weather["wind_direction"],
            "direction": wind_direction,
        },
        "sunrise_sunset": sunrise_sunset,
        "moon": moon,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/forecasts/hourly-history")
async def get_hourly_history(
    lat: float = Query(22.3193),
    lon: float = Query(114.1694),
    hours: int = Query(24, le=168)
):
    """Get historical hourly data for charts"""
    forecast = []
    base_temp = generate_weather_at_location(lat, lon, 50)["temperature"]
    
    for i in range(hours):
        hour_offset = i
        # Simulate daily temperature variation
        hour_cycle = (hour_offset % 24) / 24 * 2 * math.pi
        temp_variation = math.sin(hour_cycle) * 3
        
        aqi_base = 50 + random.uniform(-20, 20)
        pm25 = aqi_base * 0.7
        
        forecast.append({
            "hour": i,
            "timestamp": (datetime.utcnow() + timedelta(hours=i)).isoformat() + "Z",
            "temperature": round(base_temp + temp_variation + random.uniform(-1, 1), 1),
            "humidity": round(70 + random.uniform(-10, 10), 1),
            "rainfall_probability": round(random.uniform(0, 50), 1),
            "wind_speed": round(5 + random.uniform(-2, 2), 1),
            "aqi": calculate_aqi(pm25)["value"],
            "pm25": round(pm25, 1),
        })
    
    return {
        "location": {"lat": lat, "lon": lon},
        "forecast": forecast,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/weather/comparison")
async def compare_weather(
    locations: str = Query("central,mong-kok,shatin", description="Comma-separated location IDs")
):
    """Compare weather across multiple locations"""
    location_ids = locations.split(",")
    comparison = []
    
    for loc_id in location_ids:
        if loc_id.strip() in LOCATIONS:
            loc = LOCATIONS[loc_id.strip()]
            weather = generate_weather_at_location(loc["lat"], loc["lon"], 50)
            heat_index = calculate_heat_index(weather["temperature"], weather["humidity"])
            wind_chill = calculate_wind_chill(weather["temperature"], weather["wind_speed"])
            comfort = calculate_comfort_index(weather["temperature"], weather["humidity"])
            
            comparison.append({
                "id": loc_id.strip(),
                "name": loc["name"],
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "weather": weather,
                "heat_index": heat_index,
                "wind_chill": wind_chill,
                "comfort_index": comfort,
            })
    
    return {
        "comparison": comparison,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/weather/heatmap-grid")
async def get_heatmap_grid(
    bounds: str = Query("22.2,114.1,22.4,114.3", description="Bounds as min_lat,min_lon,max_lat,max_lon")
):
    """Get precipitation probability heatmap grid"""
    try:
        parts = bounds.split(",")
        min_lat, min_lon, max_lat, max_lon = map(float, parts)
    except:
        min_lat, min_lon, max_lat, max_lon = 22.2, 114.1, 22.4, 114.3
    
    grid_points = []
    step = 0.05
    
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            weather = generate_weather_at_location(lat, lon, 50)
            grid_points.append({
                "lat": lat,
                "lon": lon,
                "rainfall_probability": weather["rainfall"] * 10,  # 0-50%
                "temperature": weather["temperature"],
                "aqi": calculate_aqi(weather["pm25"])["value"],
            })
            lon += step
        lat += step
    
    return {
        "grid_points": grid_points,
        "bounds": {
            "min_lat": min_lat,
            "min_lon": min_lon,
            "max_lat": max_lat,
            "max_lon": max_lon,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
