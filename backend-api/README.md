# MicroClimate HK - Backend API

Python FastAPI backend for weather data processing and ML predictions.

## Features

- **RESTful API**: Weather data, forecasts, alerts
- **ML Integration**: Urban Canyon Model, Sensor Fusion
- **Spatial Database**: PostGIS for 3D spatial queries
- **Time-Series**: TimescaleDB for efficient weather data storage
- **Real-time**: Redis pub/sub for live updates
- **Async**: Fully asynchronous with async/await

## Setup

### Requirements

- Python 3.11+
- PostgreSQL 14+ with TimescaleDB and PostGIS
- Redis 7+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use Poetry
poetry install

# Set environment variables
cp ../.env.example .env
# Edit .env with your configuration

# Run migrations (if using Alembic)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Docker

```bash
# Build and run with docker-compose from root directory
cd ..
docker-compose up backend-api
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py              # FastAPI application
├── core/
│   └── config.py        # Configuration
├── api/
│   └── v1/              # API routes
│       ├── weather.py   # Weather endpoints
│       ├── alerts.py    # Alert endpoints
│       ├── sensors.py   # Sensor endpoints
│       ├── forecasts.py # Forecast endpoints
│       └── ml.py        # ML model endpoints
├── db/
│   ├── database.py      # Database connection
│   └── models.py        # SQLAlchemy models
├── schemas/
│   └── weather.py       # Pydantic schemas
└── services/
    ├── weather_service.py  # Weather logic
    ├── ml_service.py       # ML predictions
    └── cache.py            # Redis cache
```

## Key Endpoints

- `GET /api/weather/current` - Current weather for location
- `POST /api/weather/grid` - Weather grid for area
- `GET /api/weather/vertical` - Vertical weather profile
- `GET /api/weather/laundry-index` - Laundry dry time
- `GET /api/weather/mould-risk` - Mould risk score
- `GET /api/alerts` - Active weather alerts
- `POST /api/sensors/readings` - Submit sensor data

## Development

```bash
# Run tests
pytest

# Format code
black app/

# Lint
flake8 app/
mypy app/
```
