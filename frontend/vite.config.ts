import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API calls go to the FastAPI backend during development.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8010',
    },
  },
})
