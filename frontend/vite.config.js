import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Add base URL for production
    base: './',
  },
  // Add preview configuration
  preview: {
    port: 5173,
    host: true,
    strictPort: true,
  }
})