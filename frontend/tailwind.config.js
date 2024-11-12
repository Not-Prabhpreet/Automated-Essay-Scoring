/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#B76D68', // Indian red
          hover: '#a35f5a',   // Darker shade for hover
        },
        dark: {
          DEFAULT: '#121420', // Rich black
          card: '#1B2432',    // Gunmetal
          hover: '#2C2B3C',   // Raisin black
          input: '#403F4C',   // Onyx
        }
      }
    },
  },
  plugins: [],
}