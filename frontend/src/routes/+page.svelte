<script lang="ts">
	import { onMount } from 'svelte';
	import WeatherMap3D from '$components/map/WeatherMap3D.svelte';
	import WeatherPanel from '$components/weather/WeatherPanel.svelte';
	import AlertBar from '$components/alerts/AlertBar.svelte';
	import { weatherStore } from '$stores/weather';
	import { locationStore } from '$stores/location';

	let mapContainer: HTMLDivElement;

	onMount(async () => {
		// Initialize location (default to Central, Hong Kong)
		await locationStore.initialize();
		
		// Start fetching weather data
		await weatherStore.startUpdates();
	});
</script>

<svelte:head>
	<title>MicroClimate HK - Hyperlocal Weather for Hong Kong</title>
</svelte:head>

<main class="h-screen w-screen flex flex-col">
	<!-- Alert Bar (Typhoon warnings, etc.) -->
	<AlertBar />

	<!-- Main Content -->
	<div class="flex-1 relative">
		<!-- 3D Weather Map -->
		<div bind:this={mapContainer} class="absolute inset-0">
			<WeatherMap3D />
		</div>

		<!-- Weather Info Panel (Overlay) -->
		<div class="absolute top-20 left-4 z-10 md:top-4">
			<WeatherPanel />
		</div>

		<!-- Bottom Controls -->
		<div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
			<div class="bg-gray-900/80 backdrop-blur-md rounded-full px-6 py-3 shadow-lg">
				<div class="flex items-center space-x-4 text-sm text-gray-300">
					<button class="hover:text-white transition-colors">
						<span class="mr-2">🌡️</span> Temperature
					</button>
					<button class="hover:text-white transition-colors">
						<span class="mr-2">💧</span> Humidity
					</button>
					<button class="hover:text-white transition-colors">
						<span class="mr-2">🌧️</span> Rainfall
					</button>
					<button class="hover:text-white transition-colors">
						<span class="mr-2">💨</span> Wind
					</button>
				</div>
			</div>
		</div>
	</div>
</main>

<style>
	main {
		background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
	}
</style>
