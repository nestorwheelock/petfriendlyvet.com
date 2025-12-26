/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
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
          500: '#1E4D8C',  // Primary Blue
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
          500: '#5FAD41',  // Secondary Green
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
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        staff: {
          'primary': '#1E4D8C',
          'primary-content': '#ffffff',
          'secondary': '#5FAD41',
          'secondary-content': '#ffffff',
          'accent': '#f59e0b',
          'accent-content': '#000000',
          'neutral': '#1f2937',
          'neutral-content': '#ffffff',
          'base-100': '#ffffff',
          'base-200': '#f3f4f6',
          'base-300': '#e5e7eb',
          'base-content': '#1f2937',
          'info': '#0ea5e9',
          'success': '#22c55e',
          'warning': '#f59e0b',
          'error': '#ef4444',
        },
        superadmin: {
          'primary': '#dc2626',
          'primary-content': '#ffffff',
          'secondary': '#7c3aed',
          'secondary-content': '#ffffff',
          'accent': '#f59e0b',
          'accent-content': '#000000',
          'neutral': '#0f172a',
          'neutral-content': '#e2e8f0',
          'base-100': '#1e293b',
          'base-200': '#0f172a',
          'base-300': '#020617',
          'base-content': '#e2e8f0',
          'info': '#0ea5e9',
          'success': '#22c55e',
          'warning': '#f59e0b',
          'error': '#ef4444',
        },
      },
      'light',
      'dark',
    ],
    darkTheme: 'superadmin',
  },
}
