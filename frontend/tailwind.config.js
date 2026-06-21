/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
    },
    extend: {
      colors: {
        brand: '#C41E3A',
        light: '#F5F5F5',
        dark:  '#2C2C2C',
      }
    }
  },
  plugins: []
}
