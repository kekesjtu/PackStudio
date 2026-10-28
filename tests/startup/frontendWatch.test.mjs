import assert from 'node:assert/strict'
import { once } from 'node:events'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { setTimeout as delay } from 'node:timers/promises'
import { createServer, loadConfigFromFile } from 'vite'

test('frontend watcher skips backend and generated trees while retaining live frontend files', {
  timeout: 15000,
}, async (t) => {
  const projectRoot = fileURLToPath(new URL('../../', import.meta.url))
  const temporaryRoot = join(projectRoot, 'tmp')
  mkdirSync(temporaryRoot, { recursive: true })
  const root = mkdtempSync(join(temporaryRoot, 'frontend-watch-'))
  let server
  t.after(async () => {
    await server?.close()
    assert.equal(dirname(root), resolve(temporaryRoot))
    assert.ok(basename(root).startsWith('frontend-watch-'))
    rmSync(root, { recursive: true, force: true })
  })
  const ignoredTrees = [
    '.venv/Lib/site-packages', 'release/backend', 'build/backend',
    'tmp/test-output', 'temp/cache', '.pytest_cache', '.ruff_cache',
    'flotherm_pack_data/template', 'runtime_data/templates',
    'docs/decisions', 'figures/references', 'output_format/floxml',
    'src/packstudio/api', 'tools/__pycache__',
  ]
  const liveFiles = [
    'src/frontend/main.tsx', 'src/frontend/styles.css',
    'src/tooling/config.ts', 'public/icon.svg', 'vite.config.ts',
  ]
  for (const file of [...ignoredTrees.map(tree => `${tree}/ignored.txt`), ...liveFiles]) {
    mkdirSync(dirname(join(root, file)), { recursive: true })
    writeFileSync(join(root, file), 'initial')
  }
  const loaded = await loadConfigFromFile({ command: 'serve', mode: 'development' },
    join(projectRoot, 'vite.config.ts'))
  // Exercise the project's actual watch settings against a small, isolated repository.
  server = await createServer({
    root, configFile: false, cacheDir: join(root, 'node_modules/.vite'),
    server: {
      watch: {
        ...loaded.config.server.watch,
        ignored: loaded.config.server.watch.ignored.map(pattern => pattern.replace(
          projectRoot.replaceAll('\\', '/'), `${root.replaceAll('\\', '/')}/`)),
      },
      middlewareMode: true,
    },
    optimizeDeps: { noDiscovery: true, include: [] },
  })
  await once(server.watcher, 'ready', { signal: AbortSignal.timeout(5000) })
  // Public files can signal ready before the separate root traversal finishes.
  const liveFilesAreWatched = () => {
    const watched = server.watcher.getWatched()
    return liveFiles.every(file => watched[dirname(join(root, file))]?.includes(basename(file)))
  }
  for (let attempt = 0; attempt < 250 && !liveFilesAreWatched(); attempt++) await delay(20)
  assert.ok(liveFilesAreWatched(), 'all frontend input directories must finish initial traversal')
  const watched = Object.keys(server.watcher.getWatched()).map(path => path.replaceAll('\\', '/'))
  for (const tree of ignoredTrees) {
    const path = join(root, tree).replaceAll('\\', '/')
    assert.ok(!watched.some(directory => directory === path || directory.startsWith(`${path}/`)),
      `must not traverse ${tree}`)
  }
  for (const file of liveFiles) {
    const changed = once(server.watcher, 'change', { signal: AbortSignal.timeout(3000) })
    writeFileSync(join(root, file), 'updated')
    const [path] = await changed
    assert.equal(resolve(path), resolve(root, file))
  }
  const added = once(server.watcher, 'add', { signal: AbortSignal.timeout(3000) })
  writeFileSync(join(root, 'src/frontend/added.ts'), 'export const added = true')
  assert.equal(resolve((await added)[0]), resolve(root, 'src/frontend/added.ts'))
})
