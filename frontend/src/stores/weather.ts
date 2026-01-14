import { writable, derived } from 'svelte/store';
import type { WeatherData, MicroclimateGrid, Alert, VerticalWeatherProfile } from '$types/weather';

interface WeatherState {
	currentWeather: WeatherData | null;
	grid: MicroclimateGrid | null;
	verticalProfile: VerticalWeatherProfile | null;
	alerts: Alert[];
	loading: boolean;
	error: string | null;
	lastUpdate: Date | null;
}

function createWeatherStore() {
	const { subscribe, set, update } = writable<WeatherState>({
		currentWeather: null,
		grid: null,
		verticalProfile: null,
		alerts: [],
		loading: false,
		error: null,
		lastUpdate: null
	});

	let updateInterval: number;
	let ws: WebSocket | null = null;

	return {
		subscribe,
		
		async fetchCurrentWeather(lat: number, lng: number, elevation?: number) {
			update(state => ({ ...state, loading: true, error: null }));
			
			try {
				const elevParam = elevation ? `&elevation=${elevation}` : '';
				const response = await fetch(
					`${import.meta.env.PUBLIC_API_URL}/api/weather/current?lat=${lat}&lng=${lng}${elevParam}`
				);
				
				if (!response.ok) throw new Error('Failed to fetch weather data');
				
				const data = await response.json();
				
				update(state => ({
					...state,
					currentWeather: data,
					loading: false,
					lastUpdate: new Date()
				}));
			} catch (error) {
				update(state => ({
					...state,
					loading: false,
					error: error instanceof Error ? error.message : 'Unknown error'
				}));
			}
		},

		async fetchGrid(bounds: { minLat: number; maxLat: number; minLng: number; maxLng: number }) {
			try {
				const response = await fetch(
					`${import.meta.env.PUBLIC_API_URL}/api/weather/grid`,
					{
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ bounds, resolution: 100 })
					}
				);
				
				if (!response.ok) throw new Error('Failed to fetch grid data');
				
				const data = await response.json();
				
				update(state => ({
					...state,
					grid: data
				}));
			} catch (error) {
				console.error('Grid fetch error:', error);
			}
		},

		async fetchVerticalProfile(lat: number, lng: number, maxFloor: number = 100) {
			try {
				const response = await fetch(
					`${import.meta.env.PUBLIC_API_URL}/api/weather/vertical?lat=${lat}&lng=${lng}&maxFloor=${maxFloor}`
				);
				
				if (!response.ok) throw new Error('Failed to fetch vertical profile');
				
				const data = await response.json();
				
				update(state => ({
					...state,
					verticalProfile: data
				}));
			} catch (error) {
				console.error('Vertical profile fetch error:', error);
			}
		},

		async fetchAlerts(lat: number, lng: number, radius: number = 5000) {
			try {
				const response = await fetch(
					`${import.meta.env.PUBLIC_API_URL}/api/alerts?lat=${lat}&lng=${lng}&radius=${radius}`
				);
				
				if (!response.ok) throw new Error('Failed to fetch alerts');
				
				const alerts = await response.json();
				
				update(state => ({
					...state,
					alerts
				}));
			} catch (error) {
				console.error('Alerts fetch error:', error);
			}
		},

		connectWebSocket() {
			if (ws) return;

			ws = new WebSocket(import.meta.env.PUBLIC_WS_URL);

			ws.onmessage = (event) => {
				const data = JSON.parse(event.data);
				
				if (data.type === 'weather_update') {
					update(state => ({
						...state,
						currentWeather: data.weather,
						lastUpdate: new Date()
					}));
				} else if (data.type === 'grid_update') {
					update(state => ({
						...state,
						grid: data.grid
					}));
				} else if (data.type === 'alert') {
					update(state => ({
						...state,
						alerts: [...state.alerts, data.alert]
					}));
				}
			};

			ws.onerror = (error) => {
				console.error('WebSocket error:', error);
			};

			ws.onclose = () => {
				console.log('WebSocket closed, reconnecting in 5s...');
				setTimeout(() => {
					ws = null;
					this.connectWebSocket();
				}, 5000);
			};
		},

		disconnectWebSocket() {
			if (ws) {
				ws.close();
				ws = null;
			}
		},

		async startUpdates() {
			this.connectWebSocket();
			
			// Fallback polling every 60 seconds if WebSocket fails
			updateInterval = window.setInterval(() => {
				if (!ws || ws.readyState !== WebSocket.OPEN) {
					// Trigger refetch via location store
					console.log('Fallback: polling for updates');
				}
			}, 60000);
		},

		stopUpdates() {
			this.disconnectWebSocket();
			if (updateInterval) {
				clearInterval(updateInterval);
			}
		},

		clearError() {
			update(state => ({ ...state, error: null }));
		}
	};
}

export const weatherStore = createWeatherStore();

// Derived stores for specific weather aspects
export const temperature = derived(weatherStore, $weather => 
	$weather.currentWeather?.temperature ?? null
);

export const humidity = derived(weatherStore, $weather => 
	$weather.currentWeather?.humidity ?? null
);

export const rainfall = derived(weatherStore, $weather => 
	$weather.currentWeather?.rainfall ?? null
);

export const activeAlerts = derived(weatherStore, $weather =>
	$weather.alerts.filter(alert => {
		const now = new Date();
		return alert.validFrom <= now && alert.validUntil >= now;
	})
);
