<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { registerSW } from 'virtual:pwa-register';

	let updateSW: ((reloadPage?: boolean) => Promise<void>) | undefined;

	onMount(() => {
		// Register service worker for offline functionality
		updateSW = registerSW({
			onNeedRefresh() {
				// Show update available notification
				console.log('New version available');
			},
			onOfflineReady() {
				console.log('App ready to work offline');
			}
		});
	});
</script>

<svelte:head>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
	<meta name="theme-color" content="#0ea5e9" />
	<meta name="description" content="Block-by-block weather forecasting for Hong Kong's microclimates" />
</svelte:head>

<div class="app">
	<slot />
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
		background-color: #0f172a;
		color: #ffffff;
		overflow: hidden;
	}

	.app {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
	}
</style>
