import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Inside Docker Compose the API is reachable as http://api:8000.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // The browser only talks to this dev server; /api is forwarded to FastAPI,
    // so the session cookie stays first-party and no CORS setup is needed.
    proxy: {
      '/api': apiTarget,
      '/health': apiTarget,
    },
    // File events from a Windows bind mount do not reach the container.
    watch: process.env.CHOKIDAR_USEPOLLING ? { usePolling: true } : undefined,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
