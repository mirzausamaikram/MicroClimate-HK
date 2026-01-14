<script lang="ts">
	import { activeAlerts } from '$stores/weather';

	$: criticalAlerts = $activeAlerts.filter(a => a.severity === 'danger');
	$: warningAlerts = $activeAlerts.filter(a => a.severity === 'warning');

	function getSeverityColor(severity: string) {
		switch (severity) {
			case 'danger': return 'bg-red-600';
			case 'warning': return 'bg-yellow-600';
			default: return 'bg-blue-600';
		}
	}

	function getSeverityIcon(type: string) {
		switch (type) {
			case 'typhoon': return '🌀';
			case 'rainstorm': return '⛈️';
			case 'heat': return '🌡️';
			case 'cold': return '❄️';
			default: return '⚠️';
		}
	}
</script>

{#if $activeAlerts.length > 0}
	<div class="alert-bar fixed top-0 left-0 right-0 z-50">
		{#each $activeAlerts as alert}
			<div class="{getSeverityColor(alert.severity)} text-white px-6 py-3 flex items-center justify-between shadow-lg">
				<div class="flex items-center space-x-3">
					<span class="text-2xl">{getSeverityIcon(alert.type)}</span>
					<div>
						<div class="font-bold">{alert.title}</div>
						<div class="text-sm opacity-90">{alert.message}</div>
					</div>
				</div>
				<div class="text-xs opacity-75">
					Until {new Date(alert.validUntil).toLocaleTimeString('en-HK', { hour: '2-digit', minute: '2-digit' })}
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.alert-bar {
		animation: slideDown 0.3s ease-out;
	}

	@keyframes slideDown {
		from {
			transform: translateY(-100%);
		}
		to {
			transform: translateY(0);
		}
	}
</style>
