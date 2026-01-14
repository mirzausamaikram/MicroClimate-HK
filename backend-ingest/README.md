# MicroClimate HK - Data Ingestion Service

High-performance Go service for real-time sensor data ingestion and WebSocket updates.

## Features

- **High Throughput**: Handles 10,000+ sensor readings per minute
- **WebSocket Server**: Real-time weather updates to connected clients
- **Batch Processing**: Efficient database writes with batching
- **Data Validation**: Filters noise and outliers from crowdsourced sensors
- **Sensor Calibration**: Applies calibration offsets to improve accuracy
- **Redis Pub/Sub**: Publishes readings for other services

## Architecture

- **Worker Pool**: 10 concurrent workers for parallel processing
- **Channel-based Queue**: Buffered channels for high throughput
- **Batch Writes**: Accumulates readings and writes in batches
- **Connection Pooling**: Reuses database connections efficiently

## Setup

### Requirements

- Go 1.21+
- PostgreSQL with TimescaleDB and PostGIS
- Redis

### Installation

```bash
# Install dependencies
go mod download

# Build
go build -o bin/server ./cmd/server

# Run
./bin/server
```

### Docker

```bash
# Build and run with docker-compose from root
cd ..
docker-compose up backend-ingest
```

## Endpoints

- `POST /ingest` - Submit sensor reading
- `GET /ws` - WebSocket connection for real-time updates
- `GET /health` - Health check

## Sensor Reading Format

```json
{
  "sensor_id": "sensor-123",
  "timestamp": "2026-01-14T10:00:00Z",
  "latitude": 22.2819,
  "longitude": 114.1577,
  "elevation": 50.0,
  "temperature": 25.5,
  "humidity": 75.0,
  "rainfall": 0.0,
  "wind_speed": 5.5,
  "wind_direction": 180,
  "pressure": 1013.25,
  "device_type": "bluetooth-thermometer",
  "accuracy": 0.85
}
```

## Performance

- **Throughput**: 10,000+ readings/minute
- **Latency**: < 10ms per reading
- **Memory**: ~50MB baseline
- **CPU**: Scales with worker count
