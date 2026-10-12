import { mkdirSync, mkdtempSync, rmSync } from 'node:fs'
import { createServer } from 'node:net'
import { basename, dirname, join, resolve } from 'node:path'
import { performance } from 'node:perf_hooks'
import { fileURLToPath } from 'node:url'
import { startFrontendDev } from './start_frontend_dev.mjs'

const projectRoot = fileURLToPath(new URL('../', import.meta.url))
const cacheRoot = join(projectRoot, 'node_modules/.cache')
mkdirSync(cacheRoot, { recursive: true })
const cacheDir = mkdtempSync(join(cacheRoot, 'packstudio-startup-'))

try {
  for (const label of ['空依赖缓存', '复用依赖缓存']) {
    const socket = createServer()
    await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve))
    const port = socket.address().port
    await new Promise(resolve => socket.close(resolve))
    const start = performance.now()
    const server = await startFrontendDev({ cacheDir, port })
    try {
      const elapsed = (performance.now() - start) / 1000
      const url = `http://127.0.0.1:${server.httpServer.address().port}`
      const response = await fetch(`${url}/__packstudio/dev-ready`)
      if (response.status !== 200) throw new Error(`前端未就绪：HTTP ${response.status}`)
      console.log(`${label}：${elapsed.toFixed(3)} 秒（前端模块、样式及依赖准备）`)
    } finally {
      await server.close()
    }
  }
} finally {
  if (dirname(cacheDir) !== resolve(cacheRoot) || !basename(cacheDir).startsWith('packstudio-startup-')) {
    throw new Error('拒绝清理非本次基准测试的目录')
  }
  rmSync(cacheDir, { recursive: true, force: true })
}
