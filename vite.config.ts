import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const apiTarget = process.env.PACKSTUDIO_API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    warmup: {
      clientFiles: ['./src/frontend/main.tsx'],
    },
    proxy: {
      '/api': apiTarget,
    },
  },
  preview: {
    proxy: {
      '/api': apiTarget,
    },
  },
  test: {
    include: ['tests/frontend/**/*.test.{ts,tsx}'],
    environment: 'jsdom',
    setupFiles: ['./tests/frontend/setup.ts'],
  },
})
