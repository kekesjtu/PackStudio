import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

import frontendDependencies from './src/tooling/frontendDependencies'

const apiTarget = process.env.PACKSTUDIO_API_TARGET ?? 'http://127.0.0.1:8000'
const projectRoot = fileURLToPath(new URL('./', import.meta.url)).replaceAll('\\', '/')

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
    watch: {
      // Python environments, packaged apps and research data are not frontend inputs.
      ignored: [
        '.venv', '.pytest_cache', '.ruff_cache', 'release', 'build', 'tmp', 'temp',
        'flotherm_pack_data', 'runtime_data', 'docs', 'figures', 'output_format',
        'src/packstudio', '**/__pycache__',
      ].map(directory => `${projectRoot}${directory}/**`),
    },
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
