<script lang="ts">
	import '../app.css';
</script>

<svelte:head>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<meta name="theme-color" content="#0ea5e9" />
	<meta name="description" content="Block-by-block weather forecasting for Hong Kong's microclimates" />
</svelte:head>

<main>
	<slot />
</main>

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		height: 100%;
		width: 100%;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		background-color: #0f172a;
		color: #ffffff;
	}

	:global(*) {
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}

	main {
		width: 100%;
		height: 100%;
	}
</style>
