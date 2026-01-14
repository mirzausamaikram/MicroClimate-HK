<script>
// @ts-nocheck
	import { onMount, onDestroy } from 'svelte';

	// Theme & Language
	let isDarkMode = true;
	let language = 'en';
	let favorites = [];
	let comparisonLocations = ['central', 'mong-kok'];
	let showComparison = false;
	let comparisonData = [];

	// Weather Data
	let weather = {
		temperature: 24.5,
		humidity: 72,
		wind_speed: 5.2,
		wind_direction: 0,
		rainfall: 0,
		location: 'Central, Hong Kong',
		pm25: 35,
		aqi: { value: 50, category: "Moderate", color: "#FFFF00" }
	};

	let detailedWeather = null;
	let hourlyHistory = [];
	let laundryData = { score: 75, rating: "Good", drying_time_hours: 6, recommendations: [] };
	let mouldData = { risk_score: 50, risk_level: "Moderate", recommendations: [] };
	let forecastData = [];
	let alertsData = [];
	let locations = [];

	// UI State
	let activeTab = 'current';
	let selectedLocation = 'central';
	let showLocationDropdown = false;
	let isLoading = false;
	let error = null;
	let lastUpdated = null;
	let refreshInterval = null;

	// Translations
	const translations = {
		en: {
			title: "MicroClimate HK",
			subtitle: "Hyperlocal Weather for Hong Kong",
			current: "Current",
			forecast: "Forecast",
			indices: "Living Indices",
			chart: "Charts",
			comparison: "Compare",
			darkMode: "Dark Mode",
			language: "Language",
			favorites: "Favorites",
			addFavorite: "Add to Favorites",
			temperature: "Temperature",
			humidity: "Humidity",
			windSpeed: "Wind Speed",
			rainfall: "Rainfall",
			aqi: "Air Quality Index",
			heatIndex: "Heat Index",
			windChill: "Wind Chill",
			comfortIndex: "Comfort Index",
			sunrise: "Sunrise",
			sunset: "Sunset",
			moonPhase: "Moon Phase",
			windDirection: "Wind Direction",
			share: "Share",
		},
		'zh-hk': {
			title: "微氣候香港",
			subtitle: "香港超本地天氣",
			current: "現在",
			forecast: "預測",
			indices: "生活指數",
			chart: "圖表",
			comparison: "比較",
			darkMode: "深色模式",
			language: "語言",
			favorites: "收藏",
			addFavorite: "加入收藏",
			temperature: "溫度",
			humidity: "濕度",
			windSpeed: "風速",
			rainfall: "降雨",
			aqi: "空氣質量指數",
			heatIndex: "熱指數",
			windChill: "風寒指數",
			comfortIndex: "舒適指數",
			sunrise: "日出",
			sunset: "日落",
			moonPhase: "月相",
			windDirection: "風向",
			share: "分享",
		},
		'zh-cn': {
			title: "微气候香港",
			subtitle: "香港超本地天气",
			current: "现在",
			forecast: "预测",
			indices: "生活指数",
			chart: "图表",
			comparison: "比较",
			darkMode: "深色模式",
			language: "语言",
			favorites: "收藏",
			addFavorite: "加入收藏",
			temperature: "温度",
			humidity: "湿度",
			windSpeed: "风速",
			rainfall: "降雨",
			aqi: "空气质量指数",
			heatIndex: "热指数",
			windChill: "风寒指数",
			comfortIndex: "舒适指数",
			sunrise: "日出",
			sunset: "日落",
			moonPhase: "月相",
			windDirection: "风向",
			share: "分享",
		}
	};

	function t(key) {
		return translations[language]?.[key] || key;
	}

	onMount(() => {
		const saved = localStorage.getItem('microclimate-prefs');
		if (saved) {
			const prefs = JSON.parse(saved);
			isDarkMode = prefs.isDarkMode ?? true;
			language = prefs.language ?? 'en';
			favorites = prefs.favorites ?? [];
		}
		document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');

		fetchWeather();
		fetchAllData();
		
		refreshInterval = setInterval(() => {
			fetchWeather();
			fetchAllData();
		}, 300000);
	});

	onDestroy(() => {
		if (refreshInterval) clearInterval(refreshInterval);
	});

	function savePreferences() {
		localStorage.setItem('microclimate-prefs', JSON.stringify({ isDarkMode, language, favorites }));
	}

	function toggleTheme() {
		isDarkMode = !isDarkMode;
		document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
		savePreferences();
	}

	function changeLanguage(lang) {
		language = lang;
		savePreferences();
	}

	function toggleFavorite(locId) {
		const idx = favorites.indexOf(locId);
		if (idx > -1) {
			favorites.splice(idx, 1);
		} else {
			favorites.push(locId);
		}
		favorites = favorites;
		savePreferences();
	}

	async function fetchAllData() {
		try {
			await Promise.all([fetchForecast(), fetchAlerts(), fetchLocations(), fetchDetailedWeather(), fetchHourlyHistory()]);
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
					wind_direction: weatherData.weather.wind_direction,
					rainfall: weatherData.weather.rainfall,
					location: locationInfo?.name || 'Central, Hong Kong',
					pm25: weatherData.weather.pm25,
					aqi: weatherData.weather.aqi
				};
			}

			laundryData = laundryDataRes;
			mouldData = mouldDataRes;
			lastUpdated = new Date();
		} catch (err) {
			error = err.message || 'Failed to fetch weather data';
		} finally {
			isLoading = false;
		}
	}

	async function fetchDetailedWeather() {
		try {
			const locationInfo = locations.find(l => l.id === selectedLocation);
			const lat = locationInfo?.latitude || 22.3193;
			const lon = locationInfo?.longitude || 114.1694;
			const response = await fetch(`http://localhost:8000/api/v1/weather/detailed?lat=${lat}&lon=${lon}`);
			if (response.ok) {
				detailedWeather = await response.json();
			}
		} catch (err) {
			console.error('Failed to fetch detailed weather:', err);
		}
	}

	async function fetchHourlyHistory() {
		try {
			const locationInfo = locations.find(l => l.id === selectedLocation);
			const lat = locationInfo?.latitude || 22.3193;
			const lon = locationInfo?.longitude || 114.1694;
			const response = await fetch(`http://localhost:8000/api/v1/forecasts/hourly-history?lat=${lat}&lon=${lon}&hours=24`);
			if (response.ok) {
				const data = await response.json();
				hourlyHistory = data.forecast;
			}
		} catch (err) {
			console.error('Failed to fetch hourly history:', err);
		}
	}

	async function fetchComparison() {
		try {
			const compLocs = comparisonLocations.map(locId => {
				const loc = locations.find(l => l.id === locId);
				return { id: locId, name: loc?.name || locId, lat: loc?.latitude || 22.3193, lon: loc?.longitude || 114.1694 };
			});

			const promises = compLocs.map(async (loc) => {
				const [weatherRes, detailedRes] = await Promise.all([
					fetch(`http://localhost:8000/api/v1/weather/current?lat=${loc.lat}&lon=${loc.lon}&elevation=50`),
					fetch(`http://localhost:8000/api/v1/weather/detailed?lat=${loc.lat}&lon=${loc.lon}`)
				]);

				const weatherResp = await weatherRes.json();
				const detailed = await detailedRes.json();

				return {
					name: loc.name,
					weather: weatherResp.weather,
					heat_index: detailed.heat_index,
					comfort_index: detailed.comfort_index
				};
			});

			comparisonData = await Promise.all(promises);
		} catch (err) {
			console.error('Failed to fetch comparison:', err);
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

	async function changeLocation(locationId) {
		selectedLocation = locationId;
		showLocationDropdown = false;
		await fetchWeather();
		await fetchDetailedWeather();
		await fetchHourlyHistory();
	}

	function getWeatherEmoji(temp) {
		if (temp < 15) return '❄️';
		if (temp < 20) return '🧥';
		if (temp < 25) return '🌤️';
		if (temp < 30) return '☀️';
		return '🔥';
	}

	function formatTime(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}

	function shareWeather() {
		const text = `Current weather in ${weather.location}: ${weather.temperature}°C, ${weather.aqi.category} air quality 🌍 Check MicroClimate HK!`;
		if (navigator.share) {
			navigator.share({
				title: 'MicroClimate HK',
				text: text,
				url: window.location.href
			});
		} else {
			navigator.clipboard.writeText(`${text}\n${window.location.href}`);
			alert('Copied to clipboard!');
		}
	}

	function getWindArrow(degrees) {
		const directions = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖'];
		const idx = Math.round(degrees / 45) % 8;
		return directions[idx];
	}
</script>

<svelte:head>
	<title>MicroClimate HK - Hyperlocal Weather</title>
</svelte:head>

<div class="container">
	<!-- Header with Theme & Language Controls -->
	<header class="header">
		<div class="header-content">
			<div class="header-left">
				<h1 class="title">🌤️ {t('title')}</h1>
				<p class="subtitle">{t('subtitle')}</p>
			</div>
			<div class="header-controls">
				<button class="control-btn" on:click={toggleTheme} title={t('darkMode')}>
					{isDarkMode ? '🌙' : '☀️'}
				</button>
				<div class="language-selector">
					<button class="control-btn">🌐</button>
					<div class="lang-menu">
						<button on:click={() => changeLanguage('en')} class={language === 'en' ? 'active' : ''}>English</button>
						<button on:click={() => changeLanguage('zh-hk')} class={language === 'zh-hk' ? 'active' : ''}>繁體中文</button>
						<button on:click={() => changeLanguage('zh-cn')} class={language === 'zh-cn' ? 'active' : ''}>简体中文</button>
					</div>
				</div>
			</div>
		</div>
	</header>

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

	<!-- Main Navigation -->
	<nav class="nav">
		<div class="nav-content">
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
								<span>{loc.name}</span>
								<button
									class="favorite-btn"
									on:click|stopPropagation={() => toggleFavorite(loc.id)}
									title={favorites.includes(loc.id) ? t('addFavorite') : t('addFavorite')}
								>
									{favorites.includes(loc.id) ? '⭐' : '☆'}
								</button>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<div class="nav-tabs">
				<button class={`nav-tab ${activeTab === 'current' ? 'active' : ''}`} on:click={() => activeTab = 'current'}>
					{t('current')}
				</button>
				<button class={`nav-tab ${activeTab === 'forecast' ? 'active' : ''}`} on:click={() => activeTab = 'forecast'}>
					{t('forecast')}
				</button>
				<button class={`nav-tab ${activeTab === 'indices' ? 'active' : ''}`} on:click={() => activeTab = 'indices'}>
					{t('indices')}
				</button>
				<button class={`nav-tab ${activeTab === 'chart' ? 'active' : ''}`} on:click={() => activeTab = 'chart'}>
					{t('chart')}
				</button>
				<button class={`nav-tab ${activeTab === 'comparison' ? 'active' : ''}`} on:click={() => { activeTab = 'comparison'; fetchComparison(); }}>
					{t('comparison')}
				</button>
			</div>

			<button class="share-btn" on:click={shareWeather} title={t('share')}>
				📤 {t('share')}
			</button>
		</div>
	</nav>

	<!-- Error Message -->
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
		<!-- Current Weather Tab -->
		{#if activeTab === 'current'}
			<div class="tab-content">
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
								<p class="metric-label">💧 {t('humidity')}</p>
								<p class="metric-value">{weather.humidity.toFixed(0)}%</p>
							</div>
							<div class="metric">
								<p class="metric-label">💨 {t('windSpeed')}</p>
								<p class="metric-value">{weather.wind_speed.toFixed(1)} m/s</p>
							</div>
							<div class="metric">
								<p class="metric-label">🌧️ {t('rainfall')}</p>
								<p class="metric-value">{weather.rainfall.toFixed(1)} mm</p>
							</div>
							<div class="metric">
								<p class="metric-label">💨 PM2.5</p>
								<p class="metric-value">{weather.pm25.toFixed(1)} μg/m³</p>
							</div>
							<div class="metric">
								<p class="metric-label">{weather.aqi.category === 'Good' ? '😊' : '🙂'} {t('aqi')}</p>
								<p class="metric-value" style="color: {weather.aqi.color}">{weather.aqi.value}</p>
							</div>
						</div>
					</div>

					<!-- Indices & Advanced Metrics -->
					<div class="indices">
						<div class="index-card laundry">
							<p class="index-icon">🧺</p>
							<p class="index-label">Laundry Index</p>
							<p class="index-value">{laundryData.rating}</p>
							<p class="index-score">{laundryData.score.toFixed(0)}/100</p>
						</div>

						<div class="index-card mould">
							<p class="index-icon">🦠</p>
							<p class="index-label">Mould Risk</p>
							<p class="index-value">{mouldData.risk_level}</p>
							<p class="index-score">{mouldData.risk_score.toFixed(0)}/100</p>
						</div>

						<div class="index-card activity">
							<p class="index-icon">🏃</p>
							<p class="index-label">Outdoor Activity</p>
							<p class="index-value">{weather.temperature > 20 && weather.temperature < 30 ? 'Perfect' : 'Good'}</p>
						</div>
					</div>
				</div>

				<!-- Advanced Metrics Section -->
				{#if detailedWeather}
					<div class="advanced-metrics">
						<h3>Advanced Metrics</h3>
						<div class="metrics-grid-advanced">
							<div class="metric-card">
								<div class="metric-header">🌡️ {t('heatIndex')}</div>
								<div class="metric-value-large">{detailedWeather.heat_index}°C</div>
								<div class="metric-desc">Feels like temperature</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">❄️ {t('windChill')}</div>
								<div class="metric-value-large">{detailedWeather.wind_chill}°C</div>
								<div class="metric-desc">Wind adjusted temp</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">😊 {t('comfortIndex')}</div>
								<div class="metric-value-large">{detailedWeather.comfort_index.index}</div>
								<div class="metric-desc">{detailedWeather.comfort_index.level}</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">🧭 {t('windDirection')}</div>
								<div class="metric-value-large">{getWindArrow(detailedWeather.wind_direction.degrees)} {detailedWeather.wind_direction.direction}</div>
								<div class="metric-desc">{detailedWeather.wind_direction.degrees}°</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">🌅 {t('sunrise')}</div>
								<div class="metric-value-large">{detailedWeather.sunrise_sunset.sunrise_time}</div>
								<div class="metric-desc">Morning time</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">🌇 {t('sunset')}</div>
								<div class="metric-value-large">{detailedWeather.sunrise_sunset.sunset_time}</div>
								<div class="metric-desc">Evening time</div>
							</div>

							<div class="metric-card">
								<div class="metric-header">{detailedWeather.moon.emoji} {t('moonPhase')}</div>
								<div class="metric-value-large">{detailedWeather.moon.phase}</div>
								<div class="metric-desc">{detailedWeather.moon.illumination}% illuminated</div>
							</div>
						</div>
					</div>
				{/if}
			</div>

		<!-- Forecast Tab -->
		{:else if activeTab === 'forecast'}
			<div class="tab-content">
				<h2>24-Hour Forecast</h2>
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

		<!-- Indices Tab -->
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
				</div>
			</div>

		<!-- Chart Tab -->
		{:else if activeTab === 'chart'}
			<div class="tab-content">
				<h2>24-Hour Temperature & AQI Chart</h2>
				<div class="chart-container">
					{#if hourlyHistory.length > 0}
						<div class="chart-data">
							<table class="data-table">
								<thead>
									<tr>
										<th>Time</th>
										<th>Temperature</th>
										<th>Humidity</th>
										<th>AQI</th>
										<th>Rainfall %</th>
									</tr>
								</thead>
								<tbody>
									{#each hourlyHistory as data}
										<tr>
											<td>{formatTime(data.timestamp)}</td>
											<td>{data.temperature.toFixed(1)}°C</td>
											<td>{data.humidity.toFixed(0)}%</td>
											<td style="color: {data.aqi > 100 ? '#ff0000' : data.aqi > 50 ? '#ff7e00' : '#00e400'}">{data.aqi.toFixed(0)}</td>
											<td>{data.rainfall_probability.toFixed(0)}%</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			</div>

		<!-- Comparison Tab -->
		{:else if activeTab === 'comparison'}
			<div class="tab-content">
				<h2>Location Comparison</h2>
				<div class="comparison-grid">
					{#each comparisonData as comp}
						<div class="comparison-card">
							<h3>{comp.name}</h3>
							<div class="comp-metrics">
								<div class="comp-metric">
									<span class="comp-label">Temperature</span>
									<span class="comp-value">{comp.weather.temperature.toFixed(1)}°C</span>
								</div>
								<div class="comp-metric">
									<span class="comp-label">Humidity</span>
									<span class="comp-value">{comp.weather.humidity.toFixed(0)}%</span>
								</div>
								<div class="comp-metric">
									<span class="comp-label">Heat Index</span>
									<span class="comp-value">{comp.heat_index}°C</span>
								</div>
								<div class="comp-metric">
									<span class="comp-label">Comfort</span>
									<span class="comp-value">{comp.comfort_index.level}</span>
								</div>
								<div class="comp-metric">
									<span class="comp-label">AQI</span>
									<span class="comp-value" style="color: {comp.weather.aqi.color}">{comp.weather.aqi.value}</span>
								</div>
							</div>
						</div>
					{/each}
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
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	:global([data-theme="dark"]) {
		--bg-primary: #0f172a;
		--bg-secondary: #1e3a8a;
		--bg-tertiary: #1e293b;
		--text-primary: #ffffff;
		--text-secondary: #cbd5e1;
		--accent: #3b82f6;
		--accent-alt: #06b6d4;
		--border: rgba(59, 130, 246, 0.2);
	}

	:global([data-theme="light"]) {
		--bg-primary: #ffffff;
		--bg-secondary: #f1f5f9;
		--bg-tertiary: #e2e8f0;
		--text-primary: #0f172a;
		--text-secondary: #475569;
		--accent: #3b82f6;
		--accent-alt: #06b6d4;
		--border: rgba(59, 130, 246, 0.1);
	}

	.container {
		width: 100%;
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--bg-primary);
		color: var(--text-primary);
		transition: background-color 0.3s ease, color 0.3s ease;
	}

	.header {
		background: linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 58, 138, 0.6) 100%);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--border);
		padding: 20px 40px;
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.header-content {
		max-width: 1400px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.title {
		font-size: 28px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.subtitle {
		font-size: 14px;
		color: var(--text-secondary);
		margin: 0;
	}

	.header-controls {
		display: flex;
		gap: 15px;
		align-items: center;
	}

	.control-btn {
		background: rgba(59, 130, 246, 0.2);
		border: 1px solid var(--border);
		color: var(--accent);
		padding: 10px 12px;
		border-radius: 8px;
		cursor: pointer;
		font-size: 18px;
		transition: all 0.3s ease;
	}

	.control-btn:hover {
		background: rgba(59, 130, 246, 0.3);
		border-color: var(--accent);
	}

	.language-selector {
		position: relative;
	}

	.lang-menu {
		display: none;
		position: absolute;
		top: 100%;
		right: 0;
		background: var(--bg-tertiary);
		border: 1px solid var(--border);
		border-radius: 8px;
		margin-top: 8px;
		min-width: 120px;
		z-index: 1000;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
	}

	.language-selector:hover .lang-menu {
		display: block;
	}

	.lang-menu button {
		width: 100%;
		background: none;
		border: none;
		color: var(--text-primary);
		padding: 10px 15px;
		text-align: left;
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid var(--border);
	}

	.lang-menu button:last-child {
		border-bottom: none;
	}

	.lang-menu button:hover,
	.lang-menu button.active {
		background: rgba(59, 130, 246, 0.2);
		color: var(--accent);
		font-weight: 600;
	}

	.nav {
		background: rgba(30, 58, 138, 0.3);
		border-bottom: 1px solid var(--border);
		padding: 15px 40px;
		position: sticky;
		top: 60px;
		z-index: 99;
	}

	.nav-content {
		max-width: 1400px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 20px;
	}

	.location-selector {
		position: relative;
		flex: 0 1 300px;
	}

	.location-btn {
		width: 100%;
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
		border: 1px solid var(--border);
		color: var(--accent);
		padding: 10px 16px;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.location-btn:hover {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%);
		border-color: var(--accent);
	}

	.location-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: var(--bg-tertiary);
		border: 1px solid var(--border);
		border-radius: 8px;
		margin-top: 8px;
		max-height: 300px;
		overflow-y: auto;
		z-index: 1000;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
	}

	.location-option {
		width: 100%;
		background: none;
		border: none;
		color: var(--text-secondary);
		padding: 12px 16px;
		text-align: left;
		cursor: pointer;
		font-size: 14px;
		transition: all 0.2s ease;
		border-bottom: 1px solid var(--border);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.location-option:hover {
		background: rgba(59, 130, 246, 0.2);
		color: var(--accent);
	}

	.location-option.active {
		background: rgba(59, 130, 246, 0.3);
		color: var(--accent);
		font-weight: 600;
	}

	.favorite-btn {
		background: none;
		border: none;
		color: inherit;
		cursor: pointer;
		font-size: 16px;
		padding: 0;
		margin-left: 10px;
	}

	.nav-tabs {
		display: flex;
		gap: 10px;
		flex: 1;
	}

	.nav-tab {
		background: none;
		border: none;
		color: var(--text-secondary);
		padding: 8px 16px;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		border-bottom: 3px solid transparent;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.nav-tab:hover {
		color: var(--accent);
	}

	.nav-tab.active {
		color: var(--accent);
		border-bottom-color: var(--accent);
	}

	.share-btn {
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		border: none;
		color: white;
		padding: 10px 16px;
		border-radius: 8px;
		cursor: pointer;
		font-size: 13px;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.share-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
	}

	.main {
		flex: 1;
		max-width: 1400px;
		margin: 0 auto;
		width: 100%;
		padding: 40px;
	}

	.tab-content {
		animation: fadeInUp 0.5s ease-out;
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

	.weather-grid {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 25px;
		margin-bottom: 40px;
	}

	.weather-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
		border: 1px solid var(--border);
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

	.location {
		font-size: 16px;
		color: var(--text-secondary);
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
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.8; }
	}

	.emoji {
		font-size: 64px;
		margin: 0;
		animation: bounce 2s ease-in-out infinite;
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 15px;
		padding-top: 25px;
		border-top: 1px solid var(--border);
	}

	.metric {
		text-align: center;
	}

	.metric-label {
		font-size: 12px;
		color: var(--text-secondary);
		margin: 0 0 8px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.metric-value {
		font-size: 28px;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
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
		color: var(--text-secondary);
		margin: 0 0 8px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.index-value {
		font-size: 20px;
		font-weight: 700;
		margin: 0 0 4px 0;
		color: var(--text-primary);
	}

	.index-score {
		font-size: 14px;
		color: var(--text-secondary);
		margin: 0;
	}

	.advanced-metrics {
		margin-top: 40px;
	}

	.advanced-metrics h3 {
		margin: 0 0 20px 0;
		font-size: 20px;
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.metrics-grid-advanced {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 15px;
	}

	.metric-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 20px;
		transition: all 0.3s ease;
		text-align: center;
	}

	.metric-card:hover {
		transform: translateY(-5px);
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
	}

	.metric-header {
		font-size: 13px;
		color: var(--text-secondary);
		margin: 0 0 10px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.metric-value-large {
		font-size: 32px;
		font-weight: 700;
		margin: 0 0 8px 0;
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.metric-desc {
		font-size: 12px;
		color: var(--text-secondary);
		margin: 0;
	}

	.forecast-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 15px;
		margin-top: 20px;
	}

	.forecast-card {
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
		border: 1px solid var(--border);
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
		color: var(--text-secondary);
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
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin: 0 0 4px 0;
	}

	.humidity {
		font-size: 12px;
		color: var(--text-secondary);
		margin: 0 0 4px 0;
	}

	.rainfall {
		font-size: 12px;
		color: var(--text-secondary);
		margin: 0;
	}

	.indices-detail {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 20px;
		margin-top: 20px;
	}

	.detail-card {
		background: linear-gradient(135deg, rgba(30, 58, 138, 0.4) 0%, rgba(15, 23, 42, 0.4) 100%);
		border: 1px solid var(--border);
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
		color: var(--text-primary);
	}

	.detail-card p {
		margin: 0 0 12px 0;
		font-size: 13px;
		color: var(--text-secondary);
	}

	.detail-card ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.detail-card li {
		font-size: 13px;
		color: var(--text-secondary);
		margin-bottom: 8px;
		padding-left: 20px;
		position: relative;
	}

	.detail-card li::before {
		content: '✓';
		position: absolute;
		left: 0;
		color: var(--accent);
		font-weight: bold;
	}

	.chart-container {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 20px;
		margin-top: 20px;
		overflow-x: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
	}

	.data-table th {
		background: rgba(59, 130, 246, 0.2);
		color: var(--accent);
		padding: 12px;
		text-align: left;
		font-weight: 600;
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-bottom: 1px solid var(--border);
	}

	.data-table td {
		padding: 12px;
		border-bottom: 1px solid var(--border);
		color: var(--text-secondary);
		font-size: 13px;
	}

	.data-table tr:hover {
		background: rgba(59, 130, 246, 0.1);
	}

	.comparison-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 20px;
		margin-top: 20px;
	}

	.comparison-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 20px;
		transition: all 0.3s ease;
	}

	.comparison-card:hover {
		transform: translateY(-5px);
		border-color: rgba(59, 130, 246, 0.6);
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
	}

	.comparison-card h3 {
		margin: 0 0 16px 0;
		font-size: 18px;
		color: var(--accent);
	}

	.comp-metrics {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.comp-metric {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px;
		background: rgba(59, 130, 246, 0.1);
		border-radius: 8px;
	}

	.comp-label {
		font-size: 12px;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.comp-value {
		font-size: 14px;
		font-weight: 600;
		color: var(--accent);
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
		border: 4px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading p {
		color: var(--text-secondary);
		font-size: 14px;
	}

	.alert-banner {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(249, 115, 22, 0.2) 100%);
		border-bottom: 2px solid rgba(239, 68, 68, 0.5);
		padding: 15px 40px;
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
		color: var(--text-secondary);
	}

	.footer {
		text-align: center;
		padding: 30px;
		border-top: 1px solid var(--border);
		color: var(--text-secondary);
		font-size: 13px;
		background: linear-gradient(180deg, transparent 0%, rgba(15, 23, 42, 0.5) 100%);
	}

	.footer p {
		margin: 5px 0;
	}

	h2 {
		margin: 0 0 25px 0;
		font-size: 24px;
		background: linear-gradient(135deg, var(--accent) 0%, var(--accent-alt) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	@media (max-width: 768px) {
		.weather-grid { grid-template-columns: 1fr; }
		.indices { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: repeat(2, 1fr); }
		.nav-content { flex-direction: column; gap: 15px; }
		.nav-tabs { flex-direction: column; }
		.main { padding: 20px; }
		.header { padding: 15px 20px; }
		.header-content { flex-direction: column; }
		.title { font-size: 22px; }
		.temp { font-size: 48px; }
	}
</style>
