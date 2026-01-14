# MicroClimate HK - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   SvelteKit PWA + Deck.gl 3D Visualization + TF.js      │  │
│  │   - Progressive Web App with offline support             │  │
│  │   - WebGL-powered 3D weather visualization               │  │
│  │   - Client-side ML inference (TensorFlow Lite)           │  │
│  │   - Service Worker for offline mode                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTPS/WSS
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                             │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │  Load Balancer   │────────▶│   Rate Limiting &        │     │
│  │  (NGINX/Caddy)   │         │   Authentication         │     │
│  └──────────────────┘         └──────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      Application Services                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  FastAPI Backend │  │  Go Ingestion    │  │  WebSocket   │ │
│  │  - Weather API   │  │  - 10K+ req/min  │  │  Hub         │ │
│  │  - ML Inference  │  │  - Data Validate │  │  - Real-time │ │
│  │  - User Auth     │  │  - Batch Write   │  │  Updates     │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  TimescaleDB   │  │  Redis Cache   │  │  ML Models     │   │
│  │  + PostGIS     │  │  + Pub/Sub     │  │  Storage (S3)  │   │
│  │  - Time Series │  │  - Real-time   │  │  - TF Models   │   │
│  │  - 3D Spatial  │  │  - Session     │  │  - Offline     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     External Integrations                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  HK Observatory│  │  Lands Dept    │  │  Crowdsourced  │   │
│  │  - Official    │  │  - 3D Building │  │  - User Sensors│   │
│  │  Weather Data  │  │  Data          │  │  - Smartphones │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Real-time Weather Updates

```
User Device
    │
    ├─ WebSocket Connection ──▶ Go Ingestion Service
    │                                    │
    │                                    ├─ Validate & Calibrate
    │                                    │
    │                                    ├─ Batch Write ──▶ TimescaleDB
    │                                    │
    │                                    └─ Publish ──▶ Redis Pub/Sub
    │                                                        │
    └─ WebSocket Updates ◀─────────────────────────────────┘
```

### Weather Query Flow

```
User Request (lat, lng, elevation)
    │
    ├─ FastAPI Backend
    │     │
    │     ├─ Check Redis Cache ─────▶ Cache Hit? Return
    │     │
    │     ├─ Query TimescaleDB
    │     │     ├─ Spatial Query (PostGIS)
    │     │     └─ Time-series Query (Hypertable)
    │     │
    │     ├─ ML Interpolation
    │     │     ├─ Urban Canyon Model
    │     │     └─ Sensor Fusion Model
    │     │
    │     ├─ Cache Result (Redis)
    │     │
    │     └─ Return to User
    │
    └─ Response (JSON)
```

## Technology Stack Details

### Frontend
- **SvelteKit**: Reactive framework with excellent performance
- **Deck.gl**: WebGL 3D visualization library
- **TailwindCSS**: Utility-first styling
- **TensorFlow.js**: Client-side ML inference
- **Workbox**: Service worker for PWA

### Backend
- **Python FastAPI**: Async Python web framework
- **Go**: High-performance data ingestion
- **SQLAlchemy**: Python ORM
- **Pydantic**: Data validation

### Database
- **TimescaleDB**: Time-series PostgreSQL extension
- **PostGIS**: Spatial database extension
- **Redis**: In-memory cache and pub/sub

### ML/AI
- **TensorFlow**: Deep learning framework
- **Scikit-learn**: Traditional ML algorithms
- **XGBoost**: Gradient boosting
- **TensorFlow Lite**: Mobile/edge deployment

## Scalability Design

### Horizontal Scaling

1. **Frontend**: CDN + Static hosting (Vercel/Netlify)
2. **API Servers**: Multiple instances behind load balancer
3. **Ingestion Service**: Multiple workers processing queue
4. **Database**: Read replicas for queries, primary for writes

### Vertical Scaling

1. **Database**: TimescaleDB compression and partitioning
2. **Redis**: Cluster mode for high availability
3. **ML Models**: GPU instances for training, CPU for inference

### Caching Strategy

```
Layer 1: Browser Cache (ServiceWorker) - Offline support
    ↓
Layer 2: CDN (CloudFlare/CloudFront) - Static assets
    ↓
Layer 3: Redis Cache (5min TTL) - API responses
    ↓
Layer 4: TimescaleDB Continuous Aggregates - Pre-computed queries
    ↓
Layer 5: TimescaleDB Raw Data - Source of truth
```

## Security Architecture

### Authentication
- JWT tokens for API access
- OAuth2 for third-party integrations
- API keys for B2B customers

### Data Protection
- HTTPS/WSS for all communications
- Database encryption at rest
- Sensitive data hashing (passwords)

### Rate Limiting
- Per-user limits: 100 req/min (free), 1000 req/min (premium)
- IP-based limits: 500 req/hour (anonymous)
- Sensor submission: 10 readings/min per device

## Monitoring & Observability

### Metrics
- Application: Prometheus + Grafana
- Database: TimescaleDB stats
- Cache: Redis INFO commands

### Logging
- Structured JSON logs
- Centralized logging (ELK stack or similar)
- Error tracking (Sentry)

### Alerting
- High error rates
- Database performance degradation
- ML model accuracy drift
- Service downtime

## Disaster Recovery

### Backup Strategy
- Database: Daily full backup, continuous WAL archiving
- ML Models: Versioned in object storage
- Configuration: Version controlled (Git)

### Recovery Time Objectives
- RTO: < 1 hour for critical services
- RPO: < 15 minutes for data loss

## Cost Optimization

### Cloud Resources (Monthly Estimates)
- **Database**: $100-300 (managed TimescaleDB)
- **Compute**: $50-200 (3-5 containers)
- **Storage**: $20-50 (ML models, backups)
- **CDN**: $10-30 (frontend delivery)
- **Total**: ~$200-600/month for initial deployment

### Scaling Economics
- Free tier: Subsidized by premium users
- Premium tier ($18/month): Covers user's infrastructure cost
- B2B API: High margin revenue stream
