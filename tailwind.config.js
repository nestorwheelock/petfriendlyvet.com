/** @type {import('tailwindcss').Config} */
import daisyui from 'daisyui'
import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'

export default {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  safelist: [
    // EMR whiteboard button colors - prevent purging
    'bg-yellow-500', 'bg-yellow-600', 'hover:bg-yellow-600',
    'bg-green-500', 'bg-green-600', 'hover:bg-green-600',
    'bg-teal-500', 'bg-teal-600', 'hover:bg-teal-600',
    'bg-purple-500', 'bg-purple-600', 'hover:bg-purple-600',
    'bg-orange-500', 'bg-orange-600', 'hover:bg-orange-600',
    'bg-blue-500', 'bg-blue-600', 'hover:bg-blue-600',
    'bg-red-500', 'bg-red-600', 'hover:bg-red-600',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F0F8',
          100: '#D1E1F1',
          200: '#A3C3E3',
          300: '#75A5D5',
          400: '#4787C7',
          500: '#1E4D8C',
          600: '#183D70',
          700: '#122E54',
          800: '#0C1E38',
          900: '#060F1C',
        },
        secondary: {
          50: '#EFF8E8',
          100: '#DFF1D1',
          200: '#BFE3A3',
          300: '#9FD575',
          400: '#7FC747',
          500: '#5FAD41',
          600: '#4C8A34',
          700: '#396827',
          800: '#26451A',
          900: '#13230D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    forms,
    typography,
    daisyui,
  ],
  daisyui: {
    themes: ['light', 'dark'],
    darkTheme: 'dark',
  },
}
