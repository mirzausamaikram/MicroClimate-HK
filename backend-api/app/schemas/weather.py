from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    elevation: Optional[float] = Field(None, ge=0)


class WeatherResponse(BaseModel):
    location: Coordinates
    timestamp: datetime
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    wind_direction: Optional[float]
    pressure: Optional[float]
    uv_index: Optional[float]
    elevation: float


class GridBounds(BaseModel):
    min_lat: float = Field(..., alias="minLat")
    max_lat: float = Field(..., alias="maxLat")
    min_lng: float = Field(..., alias="minLng")
    max_lng: float = Field(..., alias="maxLng")

    class Config:
        populate_by_name = True


class WeatherGridRequest(BaseModel):
    bounds: GridBounds
    resolution: int = Field(100, ge=50, le=500)  # Grid size in meters


class GridCell(BaseModel):
    coordinates: Coordinates
    weather: WeatherResponse
    confidence: float = Field(..., ge=0, le=1)
    source: Literal["official", "crowdsourced", "interpolated", "ml-predicted"]


class WeatherGridResponse(BaseModel):
    bounds: GridBounds
    resolution: int
    data: List[GridCell]


class WeatherLayer(BaseModel):
    elevation_range: tuple[float, float]
    temperature: float
    humidity: float
    visibility: float
    rainfall: float
    wind_speed: float


class VerticalProfileResponse(BaseModel):
    location: Coordinates
    timestamp: datetime
    layers: List[WeatherLayer]


class LaundryIndexResponse(BaseModel):
    location: Coordinates
    timestamp: datetime
    dry_time_minutes: int
    mould_risk_score: float = Field(..., ge=0, le=100)
    recommendation: Literal["excellent", "good", "fair", "poor", "avoid"]
    factors: dict


class SensorReading(BaseModel):
    sensor_id: str
    location: Coordinates
    timestamp: datetime
    readings: dict
    device_type: str
    accuracy: float = Field(..., ge=0, le=1)


class AlertCreate(BaseModel):
    alert_type: Literal["typhoon", "rainstorm", "heat", "cold", "custom"]
    severity: Literal["info", "warning", "danger"]
    title: str
    message: str
    affected_area: dict
    valid_from: datetime
    valid_until: datetime


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    message: str
    affected_area: dict
    valid_from: datetime
    valid_until: datetime
    created_at: datetime
