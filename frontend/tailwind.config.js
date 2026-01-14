/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				hk: {
					blue: '#0ea5e9',
					dark: '#0f172a',
					gray: '#64748b'
				}
			},
			animation: {
				'rain-fall': 'rain-fall 1s linear infinite',
				'cloud-drift': 'cloud-drift 30s linear infinite'
			},
			keyframes: {
				'rain-fall': {
					'0%': { transform: 'translateY(-100%)' },
					'100%': { transform: 'translateY(100vh)' }
				},
				'cloud-drift': {
					'0%': { transform: 'translateX(-100%)' },
					'100%': { transform: 'translateX(100%)' }
				}
			}
		}
	},
	plugins: []
};
