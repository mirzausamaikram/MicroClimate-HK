<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Deck } from '@deck.gl/core';
	import { ScatterplotLayer, GridCellLayer } from '@deck.gl/layers';
	import { weatherStore } from '../../stores/weather';
	import { locationStore } from '../../stores/location';
	import type { MapViewState } from '../../types/weather';

	let mapContainer: HTMLDivElement;
	let deck: Deck | null = null;
	let viewState: MapViewState = {
		longitude: 114.1577,
		latitude: 22.2819,
		zoom: 12,
		pitch: 45,
		bearing: 0,
		minZoom: 10,
		maxZoom: 18
	};

	$: if ($locationStore.current) {
		viewState = {
			...viewState,
			longitude: $locationStore.current.longitude,
			latitude: $locationStore.current.latitude
		};
	}

	$: gridData = $weatherStore.grid?.data || [];

	onMount(() => {
		initializeDeck();
		weatherStore.fetchGrid({
			minLat: 22.15,
			maxLat: 22.45,
			minLng: 113.9,
			maxLng: 114.4
		});
	});

	onDestroy(() => {
		if (deck) {
			deck.finalize();
		}
	});

	function initializeDeck() {
		if (!mapContainer) return;

		deck = new Deck({
			canvas: mapContainer.querySelector('canvas') || undefined,
			width: '100%',
			height: '100%',
			initialViewState: viewState,
			controller: true,
			layers: createLayers(),
			onViewStateChange: ({ viewState: newViewState }) => {
				viewState = newViewState as MapViewState;
			}
		});
	}

	function createLayers() {
		return [
			// Temperature grid layer
			new GridCellLayer({
				id: 'temperature-grid',
				data: gridData,
				pickable: true,
				extruded: true,
				cellSize: 100,
				elevationScale: 10,
				getPosition: (d: any) => [d.coordinates.longitude, d.coordinates.latitude],
				getFillColor: (d: any) => temperatureToColor(d.weather.temperature),
				getElevation: (d: any) => d.weather.temperature * 2,
				opacity: 0.6
			}),

			// Sensor points layer
			new ScatterplotLayer({
				id: 'sensor-points',
				data: gridData.filter((d: any) => d.source === 'crowdsourced'),
				pickable: true,
				opacity: 0.8,
				stroked: true,
				filled: true,
				radiusScale: 6,
				radiusMinPixels: 3,
				radiusMaxPixels: 10,
				lineWidthMinPixels: 1,
				getPosition: (d: any) => [d.coordinates.longitude, d.coordinates.latitude, d.coordinates.elevation || 0],
				getFillColor: [0, 255, 128],
				getLineColor: [0, 0, 0],
				getRadius: (d: any) => d.confidence * 10
			})
		];
	}

	function temperatureToColor(temp: number): [number, number, number, number] {
		// Cold (blue) to hot (red) gradient
		if (temp < 15) return [0, 100, 255, 200]; // Cold blue
		if (temp < 20) return [0, 200, 255, 200]; // Cool cyan
		if (temp < 25) return [100, 255, 100, 200]; // Comfortable green
		if (temp < 30) return [255, 200, 0, 200]; // Warm yellow
		if (temp < 35) return [255, 100, 0, 200]; // Hot orange
		return [255, 0, 0, 200]; // Very hot red
	}

	$: if (deck && gridData.length > 0) {
		deck.setProps({ layers: createLayers() });
	}
</script>

<div bind:this={mapContainer} class="w-full h-full relative">
	<canvas class="w-full h-full"></canvas>
	
	<!-- Loading overlay -->
	{#if $weatherStore.loading}
		<div class="absolute inset-0 flex items-center justify-center bg-black/50">
			<div class="text-white">Loading weather data...</div>
		</div>
	{/if}

	<!-- Map attribution -->
	<div class="absolute bottom-2 right-2 text-xs text-gray-400 bg-black/50 px-2 py-1 rounded">
		Data: HKO, Crowdsourced | © MicroClimate HK
	</div>
</div>

<style>
	canvas {
		display: block;
	}
</style>
