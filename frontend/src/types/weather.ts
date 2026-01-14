export interface WeatherData {
	location: Coordinates;
	timestamp: Date;
	temperature: number;
	humidity: number;
	rainfall: number;
	windSpeed: number;
	windDirection: number;
	pressure: number;
	uvIndex: number;
	elevation: number; // Floor level or ground elevation
}

export interface Coordinates {
	latitude: number;
	longitude: number;
	elevation?: number; // Meters above sea level or floor level
}

export interface MicroclimateGrid {
	bounds: {
		minLat: number;
		maxLat: number;
		minLng: number;
		maxLng: number;
	};
	resolution: number; // Grid size in meters (e.g., 100m x 100m)
	data: GridCell[];
}

export interface GridCell {
	coordinates: Coordinates;
	weather: WeatherData;
	confidence: number; // 0-1, based on sensor density
	source: 'official' | 'crowdsourced' | 'interpolated' | 'ml-predicted';
}

export interface VerticalWeatherProfile {
	location: Coordinates;
	timestamp: Date;
	layers: WeatherLayer[];
}

export interface WeatherLayer {
	elevationRange: [number, number]; // [minFloor, maxFloor] or [minElevation, maxElevation]
	temperature: number;
	humidity: number;
	visibility: number; // For fog prediction
	rainfall: number;
	windSpeed: number;
}

export interface Alert {
	id: string;
	type: 'typhoon' | 'rainstorm' | 'heat' | 'cold' | 'custom';
	severity: 'info' | 'warning' | 'danger';
	title: string;
	message: string;
	affectedArea: {
		type: 'point' | 'radius' | 'polygon';
		coordinates: Coordinates | Coordinates[];
		radius?: number; // For radius type
	};
	validFrom: Date;
	validUntil: Date;
}

export interface SensorReading {
	sensorId: string;
	userId?: string;
	location: Coordinates;
	timestamp: Date;
	readings: {
		temperature?: number;
		humidity?: number;
		pressure?: number;
		rainfall?: number;
	};
	deviceType: 'bluetooth-thermometer' | 'smartphone-barometer' | 'weather-station' | 'other';
	accuracy: number; // Confidence score 0-1
}

export interface LaundryIndex {
	location: Coordinates;
	timestamp: Date;
	dryTimeMinutes: number;
	mouldRiskScore: number; // 0-100
	recommendation: 'excellent' | 'good' | 'fair' | 'poor' | 'avoid';
	factors: {
		temperature: number;
		humidity: number;
		sunlight: number; // 0-1
		windSpeed: number;
		buildingShadow: boolean;
	};
}

export interface BuildingData {
	buildingId: string;
	address: string;
	coordinates: Coordinates;
	height: number; // Meters
	floors: number;
	facing: 'north' | 'south' | 'east' | 'west' | 'mixed';
	surroundingBuildings: BuildingShadow[];
}

export interface BuildingShadow {
	buildingId: string;
	direction: number; // Degrees from north
	height: number;
	distance: number; // Meters
}

export interface ForecastModel {
	modelId: string;
	version: string;
	type: 'official' | 'ml-corrected' | 'crowd-sourced';
	accuracy: number;
	validFor: {
		region: 'hong-kong-island' | 'kowloon' | 'new-territories' | 'all';
		timeHorizon: number; // Hours ahead
	};
}

export interface OfflineData {
	location: Coordinates;
	radius: number; // Meters
	downloadedAt: Date;
	expiresAt: Date;
	weatherData: MicroclimateGrid;
	forecastModel: ArrayBuffer; // TensorFlow Lite model
	mapTiles: string[]; // URLs or base64 encoded tiles
	alerts: Alert[];
}

export type WeatherLayer3D = 'temperature' | 'humidity' | 'rainfall' | 'wind' | 'pressure' | 'laundry-index' | 'mould-risk';

export interface MapViewState {
	longitude: number;
	latitude: number;
	zoom: number;
	pitch: number;
	bearing: number;
	minZoom: number;
	maxZoom: number;
}
