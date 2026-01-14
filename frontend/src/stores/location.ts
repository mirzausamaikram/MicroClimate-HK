import { writable } from 'svelte/store';
import type { Coordinates } from '$types/weather';

interface LocationState {
	current: Coordinates | null;
	savedLocations: SavedLocation[];
	loading: boolean;
	error: string | null;
}

interface SavedLocation {
	id: string;
	name: string;
	coordinates: Coordinates;
	building?: string;
	floor?: number;
}

function createLocationStore() {
	const { subscribe, set, update } = writable<LocationState>({
		current: null,
		savedLocations: [],
		loading: false,
		error: null
	});

	return {
		subscribe,

		async initialize() {
			// Try to load saved location from localStorage
			const saved = localStorage.getItem('microclimate_location');
			if (saved) {
				const location = JSON.parse(saved);
				update(state => ({ ...state, current: location }));
				return;
			}

			// Try geolocation API
			if ('geolocation' in navigator) {
				update(state => ({ ...state, loading: true }));
				
				navigator.geolocation.getCurrentPosition(
					(position) => {
						const coords: Coordinates = {
							latitude: position.coords.latitude,
							longitude: position.coords.longitude,
							elevation: position.coords.altitude ?? undefined
						};
						
						update(state => ({
							...state,
							current: coords,
							loading: false
						}));
						
						localStorage.setItem('microclimate_location', JSON.stringify(coords));
					},
					(error) => {
						console.error('Geolocation error:', error);
						// Default to Central, Hong Kong
						const defaultCoords: Coordinates = {
							latitude: 22.2819,
							longitude: 114.1577
						};
						
						update(state => ({
							...state,
							current: defaultCoords,
							loading: false,
							error: 'Using default location (Central, HK)'
						}));
					}
				);
			} else {
				// Default to Central, Hong Kong
				const defaultCoords: Coordinates = {
					latitude: 22.2819,
					longitude: 114.1577
				};
				
				update(state => ({
					...state,
					current: defaultCoords
				}));
			}
		},

		setLocation(coordinates: Coordinates) {
			update(state => ({ ...state, current: coordinates }));
			localStorage.setItem('microclimate_location', JSON.stringify(coordinates));
		},

		setElevation(elevation: number) {
			update(state => {
				if (state.current) {
					const newLocation = { ...state.current, elevation };
					localStorage.setItem('microclimate_location', JSON.stringify(newLocation));
					return { ...state, current: newLocation };
				}
				return state;
			});
		},

		saveLocation(location: SavedLocation) {
			update(state => {
				const newSaved = [...state.savedLocations, location];
				localStorage.setItem('microclimate_saved_locations', JSON.stringify(newSaved));
				return { ...state, savedLocations: newSaved };
			});
		},

		removeSavedLocation(id: string) {
			update(state => {
				const newSaved = state.savedLocations.filter(loc => loc.id !== id);
				localStorage.setItem('microclimate_saved_locations', JSON.stringify(newSaved));
				return { ...state, savedLocations: newSaved };
			});
		},

		loadSavedLocations() {
			const saved = localStorage.getItem('microclimate_saved_locations');
			if (saved) {
				const locations = JSON.parse(saved);
				update(state => ({ ...state, savedLocations: locations }));
			}
		}
	};
}

export const locationStore = createLocationStore();
