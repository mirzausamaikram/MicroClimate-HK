<script lang="ts">
	import { weatherStore, temperature, humidity, rainfall } from '$stores/weather';
	import { locationStore } from '$stores/location';

	let selectedFloor = 1;
	let showVerticalProfile = false;

	$: currentLocation = $locationStore.current;
	$: currentWeather = $weatherStore.currentWeather;

	async function updateFloor(floor: number) {
		selectedFloor = floor;
		if (currentLocation) {
			await weatherStore.fetchCurrentWeather(
				currentLocation.latitude,
				currentLocation.longitude,
				floor * 3 // Approximate 3m per floor
			);
		}
	}

	function toggleVerticalProfile() {
		showVerticalProfile = !showVerticalProfile;
		if (showVerticalProfile && currentLocation) {
			weatherStore.fetchVerticalProfile(
				currentLocation.latitude,
				currentLocation.longitude,
				100 // Max 100 floors
			);
		}
	}
</script>

<div class="weather-panel bg-gray-900/90 backdrop-blur-lg rounded-2xl shadow-2xl p-6 w-96">
	<!-- Location -->
	<div class="mb-4">
		<h2 class="text-2xl font-bold text-white mb-1">
			{currentLocation ? 'Your Location' : 'Loading...'}
		</h2>
		<p class="text-gray-400 text-sm">
			{#if currentLocation}
				{currentLocation.latitude.toFixed(4)}°N, {currentLocation.longitude.toFixed(4)}°E
			{:else}
				Detecting location...
			{/if}
		</p>
	</div>

	<!-- Current Weather -->
	{#if currentWeather}
		<div class="grid grid-cols-2 gap-4 mb-6">
			<div class="bg-gradient-to-br from-orange-500 to-red-500 rounded-xl p-4">
				<div class="text-sm text-white/80 mb-1">Temperature</div>
				<div class="text-3xl font-bold text-white">{currentWeather.temperature.toFixed(1)}°C</div>
			</div>

			<div class="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl p-4">
				<div class="text-sm text-white/80 mb-1">Humidity</div>
				<div class="text-3xl font-bold text-white">{currentWeather.humidity.toFixed(0)}%</div>
			</div>

			<div class="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl p-4">
				<div class="text-sm text-white/80 mb-1">Rainfall</div>
				<div class="text-3xl font-bold text-white">{currentWeather.rainfall.toFixed(1)}mm</div>
			</div>

			<div class="bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl p-4">
				<div class="text-sm text-white/80 mb-1">Wind</div>
				<div class="text-3xl font-bold text-white">{currentWeather.windSpeed.toFixed(0)}km/h</div>
			</div>
		</div>
	{/if}

	<!-- Floor Selector -->
	<div class="mb-6">
		<div class="flex items-center justify-between mb-2">
			<label class="text-sm text-gray-300">Floor Level</label>
			<span class="text-sm font-semibold text-white">{selectedFloor}F</span>
		</div>
		<input
			type="range"
			min="1"
			max="100"
			bind:value={selectedFloor}
			on:change={() => updateFloor(selectedFloor)}
			class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
		/>
		<div class="flex justify-between text-xs text-gray-500 mt-1">
			<span>Ground</span>
			<span>100F</span>
		</div>
	</div>

	<!-- Vertical Profile Toggle -->
	<button
		on:click={toggleVerticalProfile}
		class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg"
	>
		{showVerticalProfile ? '📊 Hide' : '📊 Show'} Vertical Weather Profile
	</button>

	<!-- Vertical Profile Display -->
	{#if showVerticalProfile && $weatherStore.verticalProfile}
		<div class="mt-4 bg-gray-800 rounded-xl p-4">
			<h3 class="text-white font-semibold mb-3">Weather by Floor</h3>
			<div class="space-y-2 max-h-48 overflow-y-auto">
				{#each $weatherStore.verticalProfile.layers as layer}
					<div class="flex justify-between items-center text-sm">
						<span class="text-gray-400">F{layer.elevationRange[0]}-{layer.elevationRange[1]}</span>
						<div class="flex gap-3 text-white">
							<span>{layer.temperature.toFixed(1)}°C</span>
							<span>{layer.humidity.toFixed(0)}%</span>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Last Update -->
	{#if $weatherStore.lastUpdate}
		<div class="mt-4 text-xs text-gray-500 text-center">
			Updated {new Date($weatherStore.lastUpdate).toLocaleTimeString('en-HK')}
		</div>
	{/if}
</div>

<style>
	.slider::-webkit-slider-thumb {
		appearance: none;
		width: 20px;
		height: 20px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		cursor: pointer;
		border-radius: 50%;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
	}

	.slider::-moz-range-thumb {
		width: 20px;
		height: 20px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		cursor: pointer;
		border-radius: 50%;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
		border: none;
	}
</style>
