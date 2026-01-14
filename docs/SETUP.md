# MicroClimate HK - Complete Setup Guide

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Go 1.21+ (for ingestion service development)

### Using Docker (Recommended)

1. **Clone and configure**
   ```bash
   cd "c:\Users\mirza\New folder"
   
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configurations
   notepad .env
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - WebSocket: ws://localhost:8001/ws

### Manual Setup

#### 1. Database Setup

```bash
# Install PostgreSQL with TimescaleDB and PostGIS
# Windows: Download from https://www.timescale.com/

# Create database
psql -U postgres
CREATE DATABASE microclimate_hk;
CREATE USER microclimate WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE microclimate_hk TO microclimate;

# Initialize schema
psql -U microclimate -d microclimate_hk -f database/init.sql
```

#### 2. Redis Setup

```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### 3. Backend API (Python)

```bash
cd backend-api

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Data Ingestion Service (Go)

```bash
cd backend-ingest

# Install dependencies
go mod download

# Build and run
go build -o bin/server ./cmd/server
.\bin\server.exe
```

#### 5. Frontend (SvelteKit)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_PASSWORD=your_secure_password

# Hong Kong Observatory API
HKO_API_KEY=your_hko_api_key

# JWT Secret
JWT_SECRET=your_jwt_secret_min_32_chars

# Environment
ENVIRONMENT=development

# Frontend URLs
PUBLIC_API_URL=http://localhost:8000
PUBLIC_WS_URL=ws://localhost:8001
```

## Development Workflow

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint and format
npm run lint
npm run format
```

### Backend API Development

```bash
cd backend-api

# Activate virtual environment
venv\Scripts\activate

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/
flake8 app/

# Type checking
mypy app/
```

### Go Service Development

```bash
cd backend-ingest

# Run with auto-rebuild (use air or similar)
go run ./cmd/server

# Run tests
go test ./...

# Format code
go fmt ./...

# Build for production
go build -o bin/server ./cmd/server
```

## Training ML Models

```bash
cd ml-models

# Install dependencies
pip install -r requirements.txt

# Train Urban Canyon Model
python train_urban_canyon.py

# Train Sensor Fusion Model
python train_sensor_fusion.py

# Models will be saved to ml-models/models/
```

## API Testing

### Using curl

```bash
# Get current weather
curl "http://localhost:8000/api/weather/current?lat=22.2819&lng=114.1577"

# Get weather grid
curl -X POST "http://localhost:8000/api/weather/grid" \
  -H "Content-Type: application/json" \
  -d '{"bounds":{"minLat":22.25,"maxLat":22.35,"minLng":114.1,"maxLng":114.2},"resolution":100}'

# Get vertical profile
curl "http://localhost:8000/api/weather/vertical?lat=22.2819&lng=114.1577&max_floor=100"

# Submit sensor reading
curl -X POST "http://localhost:8001/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "test-001",
    "latitude": 22.2819,
    "longitude": 114.1577,
    "elevation": 50,
    "temperature": 25.5,
    "humidity": 75,
    "rainfall": 0,
    "wind_speed": 5.5,
    "device_type": "smartphone-barometer",
    "accuracy": 0.8
  }'
```

### Using Swagger UI

Open http://localhost:8000/docs for interactive API documentation.

## WebSocket Testing

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = () => {
  console.log('Connected to weather updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Weather update:', data);
};
```

## Production Deployment

### Build Docker Images

```bash
# Build all services
docker-compose build

# Or build individually
docker build -t microclimate-frontend ./frontend
docker build -t microclimate-api ./backend-api
docker build -t microclimate-ingest ./backend-ingest
```

### Deploy to Cloud

1. **Azure Container Apps** (Recommended for HK region)
   ```bash
   # Deploy using Azure CLI
   az containerapp create \
     --name microclimate-api \
     --resource-group microclimate-rg \
     --image microclimate-api:latest \
     --environment microclimate-env
   ```

2. **AWS ECS** (Alternative)
   ```bash
   # Push to ECR and deploy via ECS
   ```

3. **Google Cloud Run**
   ```bash
   gcloud run deploy microclimate-api \
     --image microclimate-api:latest \
     --region asia-east2
   ```

## Monitoring

- **Application Logs**: Check docker-compose logs
- **Database**: Use pgAdmin or psql
- **Redis**: Use RedisInsight
- **Performance**: Use built-in health endpoints

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs timescaledb
```

### Frontend Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules .svelte-kit
npm install
```

### Go Build Issues
```bash
# Clear module cache
go clean -modcache
go mod download
```

## Next Steps

1. ✅ Set up Hong Kong Observatory API credentials
2. ✅ Configure domain and SSL certificates
3. ✅ Set up continuous deployment
4. ✅ Configure monitoring and alerting
5. ✅ Load real building data from HK Lands Department
6. ✅ Train ML models with production data
7. ✅ Set up user authentication
8. ✅ Configure payment gateway for premium features

## Support

For issues or questions:
- Check the individual service READMEs
- Review API documentation at /docs
- Check logs using `docker-compose logs [service-name]`
