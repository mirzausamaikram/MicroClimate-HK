<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	let weather = {
		temperature: 24.5,
		humidity: 72,
		wind_speed: 5.2,
		rainfall: 0,
		location: 'Central, Hong Kong',
		pm25: 35,
		aqi: { value: 50, category: "Moderate", color: "#FFFF00" }
	};

	let laundryData = {
		score: 75,
		rating: "Good",
		drying_time_hours: 6,
		recommendations: []
	};

	let mouldData = {
		risk_score: 50,
		risk_level: "Moderate",
		recommendations: []
	};

	let forecastData: any[] = [];
	let alertsData: any[] = [];
	let locations: any[] = [];

	let activeTab: 'current' | 'forecast' | 'indices' = 'current';
	let selectedLocation = 'central';
	let showLocationDropdown = false;
	
	// State management
	let isLoading = false;
	let error: string | null = null;
	let lastUpdated: Date | null = null;
	let refreshInterval: any = null;

	onMount(() => {
		fetchWeather();
		fetchAllData();
		
		// Auto-refresh every 5 minutes
		refreshInterval = setInterval(() => {
			fetchWeather();
			fetchAllData();
		}, 300000);
	});

	onDestroy(() => {
		if (refreshInterval) clearInterval(refreshInterval);
	});

	async function fetchAllData() {
		try {
			await Promise.all([
				fetchForecast(),
				fetchAlerts(),
				fetchLocations()
			]);
		} catch (e) {
			console.error('Failed to fetch all data:', e);
		}
	}

	async function fetchWeather() {
		isLoading = true;
		error = null;
		try {
			const locationInfo = locations.find(l => l.id === selectedLocation);
			const lat = locationInfo?.latitude || 22.3193;
			const lon = locationInfo?.longitude || 114.1694;

			const [weatherRes, laundryRes, mouldRes] = await Promise.all([
				fetch(`http://localhost:8000/api/v1/weather/current?lat=${lat}&lon=${lon}&elevation=50`),
				fetch(`http://localhost:8000/api/v1/weather/laundry-index?lat=${lat}&lon=${lon}`),
				fetch(`http://localhost:8000/api/v1/weather/mould-risk?lat=${lat}&lon=${lon}`)
			]);

			if (!weatherRes.ok || !laundryRes.ok || !mouldRes.ok) throw new Error('API request failed');

			const weatherData = await weatherRes.json();
			const laundryDataRes = await laundryRes.json();
			const mouldDataRes = await mouldRes.json();

			if (weatherData.weather) {
				weather = {
					temperature: weatherData.weather.temperature,
					humidity: weatherData.weather.humidity,
					wind_speed: weatherData.weather.wind_speed,
					rainfall: weatherData.weather.rainfall,
					location: locationInfo?.name || 'Central, Hong Kong',
					pm25: weatherData.weather.pm25,
					aqi: weatherData.weather.aqi
				};
			}

			laundryData = laundryDataRes;
			mouldData = mouldDataRes;
			lastUpdated = new Date();
		} catch (err: any) {
			error = err.message || 'Failed to fetch weather data';
			console.error('Fetch error:', err);
		} finally {
			isLoading = false;
		}
	}

	async function fetchForecast() {
		try {
			const locationInfo = locations.find(l => l.id === selectedLocation);
			const lat = locationInfo?.latitude || 22.3193;
			const lon = locationInfo?.longitude || 114.1694;

			const response = await fetch(`http://localhost:8000/api/v1/forecasts/hourly?lat=${lat}&lon=${lon}&hours=48`);
			if (response.ok) {
				const data = await response.json();
				forecastData = data.forecast.slice(0, 24);
			}
		} catch (err) {
			console.error('Failed to fetch forecast:', err);
		}
	}

	async function fetchAlerts() {
		try {
			const response = await fetch('http://localhost:8000/api/v1/alerts/active');
			if (response.ok) {
				const data = await response.json();
				alertsData = data.alerts;
			}
		} catch (err) {
			console.error('Failed to fetch alerts:', err);
		}
	}

	async function fetchLocations() {
		try {
			const response = await fetch('http://localhost:8000/api/v1/locations/search');
			if (response.ok) {
				const data = await response.json();
				locations = data.results;
			}
		} catch (err) {
			console.error('Failed to fetch locations:', err);
		}
	}

	async function changeLocation(locationId: string) {
		selectedLocation = locationId;
		showLocationDropdown = false;
		await fetchWeather();
		await fetchAllData();
	}

	function getWeatherEmoji(temp: number) {
		if (temp < 15) return '❄️';
		if (temp < 20) return '🧥';
		if (temp < 25) return '🌤️';
		if (temp < 30) return '☀️';
		return '🔥';
	}

	function getAQIEmoji(category: string) {
		const emojiMap: Record<string, string> = {
			'Good': '😊',
			'Moderate': '🙂',
			'Unhealthy for Sensitive Groups': '😷',
			'Unhealthy': '😷',
			'Very Unhealthy': '💀'
		};
		return emojiMap[category] || '🤔';
	}

	function formatTime(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}
</script>

<svelte:head>
	<title>MicroClimate HK - Hyperlocal Weather</title>
</svelte:head>

<div class="container">
	<!-- Alert Banner -->
	{#if alertsData.length > 0}
		<div class="alert-banner">
			<div class="alert-content">
				<p class="alert-title">⚠️ Active Weather Alerts</p>
				{#each alertsData as alert}
					<div class="alert-item" style="border-left-color: {alert.severity === 'high' ? '#ff0000' : alert.severity === 'moderate' ? '#ff7e00' : '#ffff00'}">
						<p class="alert-type">{alert.type.toUpperCase()}</p>
						<p class="alert-message">{alert.message}</p>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Header -->
	<header class="header">
		<div class="header-content">
			<div class="header-left">
				<h1 class="title">🌤️ MicroClimate HK</h1>
				<p class="subtitle">Hyperlocal Weather for Hong Kong</p>
			</div>
			<div class="header-center">
				<div class="location-selector">
					<button class="location-btn" on:click={() => (showLocationDropdown = !showLocationDropdown)}>
						📍 {locations.find(l => l.id === selectedLocation)?.name || 'Select Location'}
					</button>
					{#if showLocationDropdown}
						<div class="location-dropdown">
							{#each locations as loc}
								<button
									class="location-option {selectedLocation === loc.id ? 'active' : ''}"
									on:click={() => changeLocation(loc.id)}
								>
									{loc.name}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>
			<div class="header-right">
				<p class="time">{new Date().toLocaleTimeString()}</p>
				{#if lastUpdated}
					<p class="last-updated">Updated: {lastUpdated.toLocaleTimeString()}</p>
				{/if}
			</div>
		</div>
	</header>

	{#if error}
		<div class="error-message">
			<p>❌ {error}</p>
			<button on:click={fetchWeather}>Retry</button>
		</div>
	{/if}

	{#if isLoading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading weather data...</p>
		</div>
	{/if}

	<!-- Main Content -->
	<main class="main">
		<!-- Current Weather Card -->
		<div class="weather-grid">
			<!-- Large Display -->
			<div class="weather-card large">
				<p class="location">{weather.location}</p>
				<div class="temperature-display">
					<p class="temp">{weather.temperature.toFixed(1)}°C</p>
					<p class="emoji">{getWeatherEmoji(weather.temperature)}</p>
				</div>

				<div class="metrics-grid">
					<div class="metric">
						<p class="metric-label">💧 Humidity</p>
						<p class="metric-value">{weather.humidity.toFixed(0)}%</p>
					</div>
					<div class="metric">
						<p class="metric-label">💨 Wind Speed</p>
						<p class="metric-value">{weather.wind_speed.toFixed(1)} m/s</p>
					</div>
					<div class="metric">
						<p class="metric-label">🌧️ Rainfall</p>
						<p class="metric-value">{weather.rainfall.toFixed(1)} mm</p>
					</div>
					<div class="metric">
						<p class="metric-label">💨 PM2.5</p>
						<p class="metric-value">{weather.pm25.toFixed(1)} μg/m³</p>
					</div>
					<div class="metric">
						<p class="metric-label">{getAQIEmoji(weather.aqi.category)} AQI</p>
						<p class="metric-value" style="color: {weather.aqi.color}">{weather.aqi.value}</p>
					</div>
				</div>
			</div>

			<!-- Smart Indices -->
			<div class="indices">
				<div class="index-card laundry">
					<p class="index-icon">🧺</p>
					<p class="index-label">Laundry Index</p>
					<p class="index-value">{laundryData.rating}</p>
					<p class="index-score">{laundryData.score.toFixed(0)}/100</p>
					<p class="index-desc">{laundryData.drying_time_hours}h drying time</p>
				</div>

				<div class="index-card mould">
					<p class="index-icon">🦠</p>
					<p class="index-label">Mould Risk</p>
					<p class="index-value">{mouldData.risk_level}</p>
					<p class="index-score">{mouldData.risk_score.toFixed(0)}/100</p>
					<p class="index-desc">Risk assessment</p>
				</div>

				<div class="index-card activity">
					<p class="index-icon">🏃</p>
					<p class="index-label">Outdoor Activity</p>
					<p class="index-value">{weather.temperature > 20 && weather.temperature < 30 ? 'Perfect' : 'Good'}</p>
					<p class="index-desc">Weather conditions</p>
				</div>
			</div>
		</div>

		<!-- Tabs -->
		<div class="tabs">
			<button
				class={`tab ${activeTab === 'current' ? 'active' : ''}`}
				on:click={() => (activeTab = 'current')}
			>
				Current
			</button>
			<button
				class={`tab ${activeTab === 'forecast' ? 'active' : ''}`}
				on:click={() => (activeTab = 'forecast')}
			>
				Forecast
			</button>
			<button
				class={`tab ${activeTab === 'indices' ? 'active' : ''}`}
				on:click={() => (activeTab = 'indices')}
			>
				Living Indices
			</button>
		</div>

		<!-- Tab Content -->
		{#if activeTab === 'forecast'}
			<div class="tab-content">
				<h2>48-Hour Forecast</h2>
				<div class="forecast-grid">
					{#each forecastData as forecast, i}
						<div class="forecast-card">
							<p class="hour">{formatTime(forecast.timestamp)}</p>
							<p class="emoji">{forecast.temperature > 20 ? '☀️' : '🌙'}</p>
							<p class="temp">{forecast.temperature.toFixed(1)}°C</p>
							<p class="humidity">💧 {forecast.humidity.toFixed(0)}%</p>
							<p class="rainfall">🌧️ {forecast.rainfall_probability.toFixed(0)}%</p>
						</div>
					{/each}
				</div>
			</div>
		{:else if activeTab === 'indices'}
			<div class="tab-content">
				<h2>Living Indices Details</h2>
				<div class="indices-detail">
					<div class="detail-card">
						<h3>🧺 Laundry Index</h3>
						<p>Score: {laundryData.score.toFixed(0)}/100 - {laundryData.rating}</p>
						<p>Drying Time: {laundryData.drying_time_hours}h</p>
						<p>Recommendations:</p>
						<ul>
							{#each laundryData.recommendations as rec}
								<li>{rec}</li>
							{/each}
						</ul>
					</div>
					<div class="detail-card">
						<h3>🦠 Mould Risk</h3>
						<p>Risk Score: {mouldData.risk_score.toFixed(0)}/100</p>
						<p>Level: {mouldData.risk_level}</p>
						<p>Recommendations:</p>
						<ul>
							{#each mouldData.recommendations as rec}
								<li>{rec}</li>
							{/each}
						</ul>
					</div>
					<div class="detail-card">
						<h3>🏃 Outdoor Activity</h3>
						<p>Temperature: {weather.temperature.toFixed(1)}°C (Ideal 20-28°C)</p>
						<ul>
							<li>✅ Air quality: {weather.aqi.category}</li>
							<li>✅ Wind speed: {weather.wind_speed.toFixed(1)} m/s</li>
							<li>✅ Humidity: {weather.humidity.toFixed(0)}%</li>
						</ul>
					</div>
				</div>
			</div>
		{:else}
			<div class="tab-content">
				<h2>Detailed Metrics</h2>
				<div class="metrics-detail">
					<div class="detail-metric">
						<span class="detail-emoji">🌡️</span>
						<div>
							<p class="detail-label">Temperature</p>
							<p class="detail-value">{weather.temperature.toFixed(1)}°C</p>
						</div>
					</div>
					<div class="detail-metric">
						<span class="detail-emoji">💧</span>
						<div>
							<p class="detail-label">Humidity</p>
							<p class="detail-value">{weather.humidity.toFixed(0)}%</p>
						</div>
					</div>
					<div class="detail-metric">
						<span class="detail-emoji">💨</span>
						<div>
							<p class="detail-label">Wind Speed</p>
							<p class="detail-value">{weather.wind_speed.toFixed(1)} m/s</p>
						</div>
					</div>
					<div class="detail-metric">
						<span class="detail-emoji">🌧️</span>
						<div>
							<p class="detail-label">Rainfall</p>
							<p class="detail-value">{weather.rainfall.toFixed(1)} mm</p>
						</div>
					</div>
					<div class="detail-metric">
						<span class="detail-emoji" style="color: {weather.aqi.color}">💨</span>
						<div>
							<p class="detail-label">Air Quality Index</p>
							<p class="detail-value" style="color: {weather.aqi.color}">{weather.aqi.value} ({weather.aqi.category})</p>
						</div>
					</div>
					<div class="detail-metric">
						<span class="detail-emoji">📊</span>
						<div>
							<p class="detail-label">PM2.5</p>
							<p class="detail-value">{weather.pm25.toFixed(1)} μg/m³</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</main>

	<!-- Footer -->
	<footer class="footer">
		<p>🇭🇰 MicroClimate HK - Hyperlocal Weather Prediction</p>
		<p>&copy; 2026 Usama Ikram. All rights reserved.</p>
	</footer>
</div>

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		color: #fff;
	}

	.container {
		width: 100%;
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
	}

	.alert-banner {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(249, 115, 22, 0.2) 100%);
		border-bottom: 2px solid rgba(239, 68, 68, 0.5);
		padding: 15px 40px;
		animation: slideDown 0.5s ease-out;
	}

	.alert-content {
		max-width: 1400px;
		margin: 0 auto;
	}

	.alert-title {
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 10px 0;
		color: #fca5a5;
	}

	.alert-item {
		background: rgba(30, 41, 59, 0.5);
		border-left: 4px solid #ff0000;
		padding: 12px 15px;
		margin-bottom: 8px;
		border-radius: 4px;
		font-size: 13px;
	}

	.alert-type {
		font-weight: 600;
		margin: 0 0 4px 0;
		text-transform: uppercase;
		color: #fca5a5;
	}

	.alert-message {
		margin: 0;
		color: #cbd5e1;
	}

	.error-message {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(249, 115, 22, 0.2) 100%);
		border: 1px solid rgba(239, 68, 68, 0.5);
		border-radius: 8px;
		padding: 15px 20px;
		margin: 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		animation: slideDown 0.3s ease-out;
	}

	.error-message p {
		margin: 0;
		color: #fca5a5;
	}

	.error-message button {
		background: rgba(239, 68, 68, 0.3);
		border: 1px solid rgba(239, 68, 68, 0.6);
		color: #fca5a5;
		padding: 8px 16px;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.error-message button:hover {
		background: rgba(239, 68, 68, 0.5);
	}

	.loading {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 60px 20px;
		gap: 20px;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(59, 130, 246, 0.2);
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading p {
		color: #94a3b8;
		font-size: 14px;
	}

	.header {
		background: linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 58, 138, 0.6) 100%);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid rgba(59, 130, 246, 0.2);
		padding: 20px 40px;
		position: sticky;
		top: 0;
		z-index: 100;
		animation: slideDown 0.5s ease-out;
	}

	@keyframes slideDown {
		from {
			transform: translateY(-50px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.header-content {
		max-width: 1400px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 30px;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 15px;
		flex: 0 0 auto;
	}

	.header-center {
		flex: 1;
		display: flex;
		justify-content: center;
	}

	.location-selector {
		position: relative;
	}

	.location-btn {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
		border: 1px solid rgba(59, 130, 246, 0.4);
		color: #3b82f6;
		padding: 10px 16px;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.location-btn:hover {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%);
		border-color: rgba(59, 130, 246, 0.6);
	}

	.location-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 58, 138, 0.95) 100%);
		border: 1px solid rgba(59, 130, 246, 0.3);
		border-radius: 8px;
		margin-top: 8px;
		max-height: 300px;
		overflow-y: auto;
		z-index: 1000;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
		animation: slideDown 0.2s ease-out;
	}

	.location-option {
		width: 100%;
		background: none;
		border: none;
		color: #cbd5e1;
		padding: 12px 16px;
		text-align: left;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(59, 130, 246, 0.1);
	}

	.location-option:hover {
		background: rgba(59, 130, 246, 0.2);
		color: #3b82f6;
	}

	.location-option.active {
		background: rgba(59, 130, 246, 0.3);
		color: #3b82f6;
		font-weight: 600;
	}

	.header-right {
		display: flex;
		flex-direction: column;
		text-align: right;
		gap: 4px;
		flex: 0 0 auto;
	}

	.title {
		font-size: 28px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.subtitle {
		font-size: 14px;
		color: #94a3b8;
		margin: 0;
		margin-top: 5px;
	}

	.time {
		font-size: 14px;
		color: #cbd5e1;
		font-family: 'Courier New', monospace;
		margin: 0;
	}

	.last-updated {
		font-size: 12px;
		color: #64748b;
		margin: 0;
	}
	.main {
		flex: 1;
		max-width: 1400px;
		margin: 0 auto;
		width: 100%;
		padding: 40px;
	}

	.weather-grid {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 25px;
		margin-bottom: 40px;
		animation: fadeInUp 0.6s ease-out;
	}

	@keyframes fadeInUp {
		from {
			transform: translateY(20px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.weather-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
		border: 1px solid rgba(59, 130, 246, 0.3);
		border-radius: 24px;
		padding: 35px;
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
	}

	.weather-card:hover {
		transform: translateY(-5px);
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%);
		box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
	}

	.weather-card.large {
		grid-column: span 1;
	}

	.location {
		font-size: 16px;
		color: #cbd5e1;
		margin: 0 0 20px 0;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.temperature-display {
		display: flex;
		align-items: center;
		gap: 25px;
		margin-bottom: 30px;
	}

	.temp {
		font-size: 72px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.8;
		}
	}

	.emoji {
		font-size: 64px;
		margin: 0;
		animation: bounce 2s ease-in-out infinite;
	}

	@keyframes bounce {
		0%, 100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-10px);
		}
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 15px;
		padding-top: 25px;
		border-top: 1px solid rgba(59, 130, 246, 0.2);
	}

	.metric {
		text-align: center;
	}

	.metric-label {
		font-size: 12px;
		color: #94a3b8;
		margin: 0 0 8px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.metric-value {
		font-size: 28px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.indices {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 15px;
	}

	.index-card {
		border-radius: 16px;
		padding: 20px;
		backdrop-filter: blur(10px);
		text-align: center;
		transition: all 0.3s ease;
		border: 1px solid transparent;
	}

	.index-card:hover {
		transform: translateY(-8px);
		box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
	}

	.index-card.laundry {
		background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%);
		border-color: rgba(168, 85, 247, 0.3);
	}

	.index-card.laundry:hover {
		border-color: rgba(168, 85, 247, 0.6);
		background: linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(236, 72, 153, 0.25) 100%);
	}

	.index-card.mould {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%);
		border-color: rgba(239, 68, 68, 0.3);
	}

	.index-card.mould:hover {
		border-color: rgba(239, 68, 68, 0.6);
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(249, 115, 22, 0.25) 100%);
	}

	.index-card.activity {
		background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
		border-color: rgba(34, 197, 94, 0.3);
	}

	.index-card.activity:hover {
		border-color: rgba(34, 197, 94, 0.6);
		background: linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(5, 150, 105, 0.25) 100%);
	}

	.index-icon {
		font-size: 32px;
		margin: 0 0 8px 0;
	}

	.index-label {
		font-size: 12px;
		color: #94a3b8;
		margin: 0 0 8px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.index-value {
		font-size: 20px;
		font-weight: 700;
		margin: 0 0 4px 0;
		color: #fff;
	}

	.index-score {
		font-size: 14px;
		color: #cbd5e1;
		margin: 0 0 4px 0;
	}

	.index-desc {
		font-size: 11px;
		color: #cbd5e1;
		margin: 0;
	}

	.tabs {
		display: flex;
		gap: 20px;
		margin-bottom: 30px;
		border-bottom: 1px solid rgba(59, 130, 246, 0.2);
		animation: fadeIn 0.6s ease-out 0.2s both;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.tab {
		background: none;
		border: none;
		color: #94a3b8;
		padding: 12px 20px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		border-bottom: 3px solid transparent;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.tab:hover {
		color: #3b82f6;
	}

	.tab.active {
		color: #3b82f6;
		border-bottom-color: #3b82f6;
		box-shadow: 0 3px 0 rgba(59, 130, 246, 0.3);
	}

	.tab-content {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 16px;
		padding: 30px;
		backdrop-filter: blur(10px);
		animation: fadeInUp 0.5s ease-out;
	}

	.tab-content h2 {
		margin: 0 0 25px 0;
		font-size: 24px;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.forecast-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 15px;
	}

	.forecast-card {
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 12px;
		padding: 15px;
		text-align: center;
		transition: all 0.3s ease;
		cursor: pointer;
	}

	.forecast-card:hover {
		transform: translateY(-5px);
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
	}

	.hour {
		font-size: 12px;
		color: #94a3b8;
		margin: 0 0 8px 0;
		font-weight: 600;
	}

	.forecast-card .emoji {
		font-size: 32px;
		margin: 0 0 8px 0;
		animation: none;
	}

	.forecast-card .temp {
		font-size: 20px;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin: 0 0 4px 0;
	}

	.humidity {
		font-size: 12px;
		color: #cbd5e1;
		margin: 0 0 4px 0;
	}

	.rainfall {
		font-size: 12px;
		color: #cbd5e1;
		margin: 0;
	}

	.indices-detail {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 20px;
	}

	.detail-card {
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.4) 0%, rgba(15, 23, 42, 0.4) 100%);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 12px;
		padding: 20px;
		transition: all 0.3s ease;
	}

	.detail-card:hover {
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
		transform: translateY(-5px);
	}

	.detail-card h3 {
		margin: 0 0 12px 0;
		font-size: 16px;
		color: #fff;
	}

	.detail-card p {
		margin: 0 0 12px 0;
		font-size: 13px;
		color: #94a3b8;
	}

	.detail-card ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.detail-card li {
		font-size: 13px;
		color: #cbd5e1;
		margin-bottom: 8px;
		padding-left: 20px;
		position: relative;
	}

	.detail-card li::before {
		content: '✓';
		position: absolute;
		left: 0;
		color: #3b82f6;
		font-weight: bold;
	}

	.metrics-detail {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}

	.detail-metric {
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
		border: 1px solid rgba(59, 130, 246, 0.2);
		border-radius: 12px;
		padding: 20px;
		display: flex;
		align-items: center;
		gap: 15px;
		transition: all 0.3s ease;
	}

	.detail-metric:hover {
		transform: translateY(-5px);
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
	}

	.detail-emoji {
		font-size: 32px;
	}

	.detail-label {
		font-size: 12px;
		color: #94a3b8;
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.detail-value {
		font-size: 24px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.footer {
		text-align: center;
		padding: 30px;
		border-top: 1px solid rgba(59, 130, 246, 0.2);
		color: #64748b;
		font-size: 13px;
		background: linear-gradient(180deg, transparent 0%, rgba(15, 23, 42, 0.5) 100%);
	}

	.footer p {
		margin: 5px 0;
	}

	@media (max-width: 768px) {
		.weather-grid {
			grid-template-columns: 1fr;
		}

		.indices {
			grid-template-columns: 1fr;
		}

		.metrics-grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.main {
			padding: 20px;
		}

		.header {
			padding: 15px 20px;
		}

		.header-content {
			flex-direction: column;
			gap: 15px;
		}

		.header-center {
			flex: none;
		}

		.header-right {
			align-items: center;
		}

		.title {
			font-size: 22px;
		}

		.temp {
			font-size: 48px;
		}

		.emoji {
			font-size: 48px;
		}
	}
</style>
