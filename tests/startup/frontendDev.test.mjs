import assert from 'node:assert/strict'
import { once } from 'node:events'
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { createServer as createSocketServer } from 'node:net'
import { basename, dirname, join, resolve } from 'node:path'
import { setTimeout as delay } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

import { startFrontendDev } from '../../tools/start_frontend_dev.mjs'

test('development readiness waits for transforms and the server still updates changed source', {
  timeout: 30000,
}, async (t) => {
  const temporaryRoot = fileURLToPath(new URL('../../tmp/', import.meta.url))
  const projectMetadata = fileURLToPath(new URL('../../node_modules/.vite/deps/_metadata.json', import.meta.url))
  const metadataBefore = existsSync(projectMetadata) ? readFileSync(projectMetadata, 'utf8') : null
  mkdirSync(temporaryRoot, { recursive: true })
  const root = mkdtempSync(join(temporaryRoot, 'dev-server-test-'))
  const cacheDir = join(root, '.vite')
  let server
  t.after(async () => {
    await server?.close()
    assert.equal(dirname(root), resolve(temporaryRoot))
    assert.ok(basename(root).startsWith('dev-server-test-'))
    rmSync(root, { recursive: true, force: true })
    const metadataAfter = existsSync(projectMetadata) ? readFileSync(projectMetadata, 'utf8') : null
    assert.equal(metadataAfter, metadataBefore, 'startup tests must preserve the real development cache')
  })
  mkdirSync(join(root, 'src/frontend'), { recursive: true })
  writeFileSync(join(root, 'index.html'), '<script type="module" src="/src/frontend/main.tsx"></script>')
  writeFileSync(join(root, 'vite.config.mjs'), `export default {
    css: { postcss: { plugins: [] } },
    optimizeDeps: { noDiscovery: true },
    plugins: [{ name: 'slow-first-transform', async transform(code, id) {
      if (id.endsWith('/main.tsx')) await new Promise(resolve => setTimeout(resolve, 700));
    } }]
  }`)
  const entry = join(root, 'src/frontend/main.tsx')
  writeFileSync(entry, "export const label = 'initial-content'")
  const socketServer = createSocketServer()
  await new Promise(resolve => socketServer.listen(0, '127.0.0.1', resolve))
  const port = socketServer.address().port
  await new Promise(resolve => socketServer.close(resolve))
  const startup = startFrontendDev({ root, port, cacheDir, configFile: join(root, 'vite.config.mjs') })
  const url = `http://127.0.0.1:${port}`
  let initialStatus
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      initialStatus = (await fetch(`${url}/__packstudio/dev-ready`)).status
      break
    } catch { await delay(20) }
  }
  server = await startup
  assert.equal(server.config.cacheDir, cacheDir.replaceAll('\\', '/'))
  assert.equal(initialStatus, 503)
  const ready = await fetch(`${url}/__packstudio/dev-ready`)
  assert.equal(ready.status, 200)
  assert.deepEqual(await ready.json(), { ready: true })
  assert.match(await (await fetch(`${url}/src/frontend/main.tsx`)).text(), /initial-content/)
  const changed = once(server.watcher, 'change', { signal: AbortSignal.timeout(5000) })
  writeFileSync(entry, "export const label = 'updated-content'")
  await changed
  assert.match(await (await fetch(`${url}/src/frontend/main.tsx`)).text(), /updated-content/)
})
