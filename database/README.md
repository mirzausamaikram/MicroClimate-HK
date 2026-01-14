# Database Schemas

TimescaleDB and PostGIS schemas for MicroClimate HK.

## Structure

- **weather_readings**: Time-series weather data (hypertable)
- **sensor_stations**: Crowdsourced sensor metadata
- **weather_alerts**: Active weather alerts and warnings
- **building_data**: Hong Kong building information
- **forecast_data**: ML model predictions
- **users**: User accounts and preferences

## Features

- TimescaleDB hypertables for efficient time-series queries
- PostGIS 3D spatial indexing (POINTZ geometry)
- Continuous aggregates for hourly weather data
- Data retention policies
- Spatial indexes for fast location-based queries

## Setup

```bash
# Run initialization script
psql -U microclimate -d microclimate_hk -f init.sql

# Or use Docker
docker-compose up timescaledb
# Database will be automatically initialized
```

## Queries

### Get weather near location
```sql
SELECT * FROM weather_readings
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(114.1577, 22.2819, 0), 4326),
    1000  -- 1km radius
)
AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Get vertical weather profile
```sql
SELECT 
    FLOOR(ST_Z(location) / 30) * 30 as elevation_bucket,
    AVG(temperature) as avg_temp,
    AVG(humidity) as avg_humidity
FROM weather_readings
WHERE ST_DWithin(
    ST_SetSRID(ST_MakePoint(114.1577, 22.2819), 4326),
    location,
    500
)
AND timestamp > NOW() - INTERVAL '30 minutes'
GROUP BY elevation_bucket
ORDER BY elevation_bucket;
```

### Get buildings in area
```sql
SELECT 
    building_id,
    address,
    height_meters,
    floors
FROM building_data
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(114.1577, 22.2819), 4326),
    2000
)
ORDER BY ST_Distance(location, ST_SetSRID(ST_MakePoint(114.1577, 22.2819), 4326));
```

## Performance

- Spatial indexes using GIST
- Time partitioning via TimescaleDB
- Continuous aggregates for common queries
- Query optimization for Hong Kong geography
