import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

import frontendDependencies from './src/tooling/frontendDependencies'

const apiTarget = process.env.PACKSTUDIO_API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  css: {
    // The project uses plain CSS; avoid searching parent directories for PostCSS config.
    postcss: { plugins: [] },
  },
  optimizeDeps: {
    entries: ['index.html'],
    noDiscovery: true,
    include: frontendDependencies(fileURLToPath(new URL('./src/frontend', import.meta.url))),
  },
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
