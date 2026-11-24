/** @type {import('tailwindcss').Config} */
// Colours are CSS variables (src/index.css) so light and dark are each chosen, not flipped.
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: v('paper'),
        surface: v('surface'),
        sunk: v('sunk'),
        ink: v('ink'),
        ink2: v('ink2'),
        muted: v('muted'),
        rule: v('rule'),
        accent: v('accent'),
        'accent-ink': v('accent-ink'),
        'accent-soft': v('accent-soft'),
        pen: v('pen'),
        'pen-soft': v('pen-soft'),
        ochre: v('ochre'),
        'chart-new': v('chart-new'),
        'chart-base': v('chart-base'),
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      maxWidth: { prose: '68ch' },
    },
  },
  plugins: [],
};
