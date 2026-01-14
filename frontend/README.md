# MicroClimate HK - Frontend

SvelteKit Progressive Web App with 3D weather visualization.

## Features

- **3D Weather Visualization**: WebGL-powered deck.gl integration
- **Offline-First**: PWA with service worker and IndexedDB caching
- **Region-Specific Code Splitting**: Load only relevant geographical data
- **Real-time Updates**: WebSocket integration for live sensor data
- **TensorFlow.js**: Client-side ML inference for offline forecasting

## Tech Stack

- **Framework**: SvelteKit
- **Styling**: TailwindCSS
- **3D Graphics**: Deck.gl, Luma.gl, Three.js
- **ML**: TensorFlow.js
- **Offline**: Workbox, sql.js (SQLite in WASM)

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── routes/              # SvelteKit pages
├── components/          # Reusable UI components
│   ├── map/            # 3D map components
│   ├── weather/        # Weather display widgets
│   └── alerts/         # Alert notifications
├── lib/                # Utilities and APIs
│   ├── api/            # API client
│   ├── weather/        # Weather data processing
│   ├── spatial/        # Geospatial utilities
│   └── ml/             # TensorFlow.js models
├── stores/             # Svelte stores (state management)
├── types/              # TypeScript definitions
└── workers/            # Web Workers and Service Workers
```

## Environment Variables

Create `.env` file:

```
PUBLIC_API_URL=http://localhost:8000
PUBLIC_WS_URL=ws://localhost:8001
```

## HK-Specific Optimizations

- **Code Splitting**: Separate bundles for Kowloon, HK Island, New Territories
- **3D Terrain Tiles**: Pre-rendered for each district
- **Compressed Sensor Data**: Efficient binary format for mobile networks
