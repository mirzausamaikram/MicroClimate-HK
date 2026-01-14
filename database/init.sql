-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Weather Readings Table (TimescaleDB Hypertable)
CREATE TABLE IF NOT EXISTS weather_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    location GEOMETRY(POINTZ, 4326) NOT NULL,
    
    -- Weather measurements
    temperature DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    rainfall DOUBLE PRECISION DEFAULT 0.0,
    wind_speed DOUBLE PRECISION NOT NULL,
    wind_direction DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    uv_index DOUBLE PRECISION,
    
    -- Metadata
    source VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    sensor_id VARCHAR(255)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('weather_readings', 'timestamp', if_not_exists => TRUE);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_readings USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_weather_time_location ON weather_readings(timestamp, location);
CREATE INDEX IF NOT EXISTS idx_weather_sensor ON weather_readings(sensor_id);

-- Sensor Stations Table
CREATE TABLE IF NOT EXISTS sensor_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID,
    
    location GEOMETRY(POINTZ, 4326) NOT NULL,
    device_type VARCHAR(100) NOT NULL,
    
    -- Calibration
    temperature_offset DOUBLE PRECISION DEFAULT 0.0,
    humidity_offset DOUBLE PRECISION DEFAULT 0.0,
    accuracy_score DOUBLE PRECISION DEFAULT 0.5,
    
    -- Metadata
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_reading_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sensor_location ON sensor_stations USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_sensor_id ON sensor_stations(sensor_id);

-- Weather Alerts Table
CREATE TABLE IF NOT EXISTS weather_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Spatial extent
    affected_area GEOMETRY(POLYGON, 4326),
    center_point GEOMETRY(POINT, 4326),
    radius_meters DOUBLE PRECISION,
    
    -- Validity
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_alert_area ON weather_alerts USING GIST(affected_area);
CREATE INDEX IF NOT EXISTS idx_alert_validity ON weather_alerts(valid_from, valid_until);

-- Building Data Table
CREATE TABLE IF NOT EXISTS building_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id VARCHAR(255) UNIQUE NOT NULL,
    
    address TEXT,
    location GEOMETRY(POINT, 4326) NOT NULL,
    
    -- Building characteristics
    height_meters DOUBLE PRECISION NOT NULL,
    floors INTEGER,
    facing VARCHAR(20),
    
    -- Footprint
    footprint GEOMETRY(POLYGON, 4326),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_building_location ON building_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_building_footprint ON building_data USING GIST(footprint);
CREATE INDEX IF NOT EXISTS idx_building_id ON building_data(building_id);

-- Forecast Data Table
CREATE TABLE IF NOT EXISTS forecast_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Forecast metadata
    forecast_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_time TIMESTAMPTZ NOT NULL,
    lead_time_hours INTEGER NOT NULL,
    
    location GEOMETRY(POINTZ, 4326) NOT NULL,
    
    -- Predicted weather
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    
    -- Model metadata
    model_id VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    confidence DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_forecast_location ON forecast_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_forecast_valid_time ON forecast_data(valid_time);

-- User Table (for crowdsourcing)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile
    display_name VARCHAR(100),
    
    -- Preferences
    saved_locations JSONB DEFAULT '[]',
    
    -- Premium
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Data retention policies (optional - for production)
-- Keep raw sensor data for 30 days, then downsample
-- SELECT add_retention_policy('weather_readings', INTERVAL '30 days');

-- Create continuous aggregates for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS weather_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    ST_SnapToGrid(location, 0.001) AS grid_location,
    AVG(temperature) AS avg_temperature,
    AVG(humidity) AS avg_humidity,
    AVG(rainfall) AS avg_rainfall,
    AVG(wind_speed) AS avg_wind_speed,
    COUNT(*) AS reading_count
FROM weather_readings
GROUP BY hour, grid_location
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('weather_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Sample data for testing (Hong Kong locations)
INSERT INTO building_data (building_id, address, location, height_meters, floors, facing) VALUES
    ('ifc-hk', 'International Finance Centre', ST_SetSRID(ST_MakePoint(114.1580, 22.2855), 4326), 420, 88, 'mixed'),
    ('icc-kowloon', 'International Commerce Centre', ST_SetSRID(ST_MakePoint(114.1636, 22.3045), 4326), 484, 118, 'mixed'),
    ('the-peak', 'The Peak Tower', ST_SetSRID(ST_MakePoint(114.1497, 22.2708), 4326), 428, 5, 'mixed')
ON CONFLICT (building_id) DO NOTHING;

COMMIT;
