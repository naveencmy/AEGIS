/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#06090F',
          900: '#0A0E17',
          850: '#0F1523',
          800: '#141D30',
          750: '#1A253D',
          700: '#22304F'
        },
        cyber: {
          indigo: '#6366F1',
          'indigo-glow': '#818CF8',
          cyan: '#06B6D4',
          'cyan-glow': '#22D3EE',
          emerald: '#10B981',
          crimson: '#EF4444',
          amber: '#F59E0B'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace']
      },
      animation: {
        'pulse-glow': 'pulseGlow 2.5s infinite ease-in-out',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      }
    },
  },
  plugins: [],
}
