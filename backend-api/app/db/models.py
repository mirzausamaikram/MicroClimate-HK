from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

from app.db.database import Base


class WeatherReading(Base):
    """Weather reading model"""
    __tablename__ = "weather_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    location = Column(Geometry('POINTZ', srid=4326), nullable=False)  # 3D point (lat, lng, elevation)
    
    # Weather measurements
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall = Column(Float, default=0.0)
    wind_speed = Column(Float, nullable=False)
    wind_direction = Column(Float)
    pressure = Column(Float)
    uv_index = Column(Float)
    
    # Metadata
    source = Column(String, nullable=False)  # 'official', 'crowdsourced', 'interpolated', 'ml-predicted'
    confidence = Column(Float, default=1.0)
    sensor_id = Column(String, index=True)
    
    __table_args__ = (
        Index('idx_weather_location', 'location', postgresql_using='gist'),
        Index('idx_weather_time_location', 'timestamp', 'location'),
    )


class SensorStation(Base):
    """Sensor station model (crowdsourced and official)"""
    __tablename__ = "sensor_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    
    location = Column(Geometry('POINTZ', srid=4326), nullable=False)
    device_type = Column(String, nullable=False)
    
    # Calibration data
    temperature_offset = Column(Float, default=0.0)
    humidity_offset = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.5)
    
    # Metadata
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reading_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_sensor_location', 'location', postgresql_using='gist'),
    )


class WeatherAlert(Base):
    """Weather alert model"""
    __tablename__ = "weather_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String, nullable=False)  # 'typhoon', 'rainstorm', 'heat', 'cold'
    severity = Column(String, nullable=False)  # 'info', 'warning', 'danger'
    
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    # Spatial extent
    affected_area = Column(Geometry('POLYGON', srid=4326))
    center_point = Column(Geometry('POINT', srid=4326))
    radius_meters = Column(Float)
    
    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default='system')
    
    __table_args__ = (
        Index('idx_alert_area', 'affected_area', postgresql_using='gist'),
        Index('idx_alert_validity', 'valid_from', 'valid_until'),
    )


class BuildingData(Base):
    """Building data model"""
    __tablename__ = "building_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(String, unique=True, nullable=False, index=True)
    
    address = Column(String)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    
    # Building characteristics
    height_meters = Column(Float, nullable=False)
    floors = Column(Integer)
    facing = Column(String)  # 'north', 'south', 'east', 'west', 'mixed'
    
    # Footprint
    footprint = Column(Geometry('POLYGON', srid=4326))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_building_location', 'location', postgresql_using='gist'),
        Index('idx_building_footprint', 'footprint', postgresql_using='gist'),
    )


class ForecastData(Base):
    """ML forecast model predictions"""
    __tablename__ = "forecast_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Forecast metadata
    forecast_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    valid_time = Column(DateTime, nullable=False, index=True)
    lead_time_hours = Column(Integer, nullable=False)
    
    location = Column(Geometry('POINTZ', srid=4326), nullable=False)
    
    # Predicted weather
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    wind_speed = Column(Float)
    
    # Model metadata
    model_id = Column(String, nullable=False)
    model_version = Column(String)
    confidence = Column(Float)
    
    __table_args__ = (
        Index('idx_forecast_location', 'location', postgresql_using='gist'),
        Index('idx_forecast_valid_time', 'valid_time'),
    )
