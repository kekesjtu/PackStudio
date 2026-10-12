import { resolve } from 'node:path'
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { parseArgs } from 'node:util'
import { createServer } from 'vite'

const projectRoot = fileURLToPath(new URL('../', import.meta.url))

export async function startFrontendDev({
  root = projectRoot, host = '127.0.0.1', port = 5173,
  configFile = resolve(root, 'vite.config.ts'), cacheDir, force = false,
} = {}) {
  let ready = false
  const server = await createServer({
    root, configFile, cacheDir, optimizeDeps: { force },
    server: { host, port, strictPort: true, preTransformRequests: false },
    plugins: [{
      name: 'packstudio-dev-readiness',
      configureServer(server) {
        server.middlewares.use((request, response, next) => {
          if (request.url !== '/__packstudio/dev-ready') return next()
          response.statusCode = ready ? 200 : 503
          response.setHeader('Content-Type', 'application/json')
          response.end(JSON.stringify({ ready }))
        })
      },
    }],
  })
  try {
    await server.listen()
    const client = server.environments.client
    const frontendDirectory = resolve(root, 'src/frontend')
    const sourceFiles = readdirSync(frontendDirectory, { recursive: true })
      .filter(file => typeof file === 'string' && /\.(tsx?|css)$/.test(file) && !file.endsWith('.d.ts'))
    await Promise.all(sourceFiles.map(file =>
      client.transformRequest('/src/frontend/' + file.replaceAll('\\', '/'))))
    await client.waitForRequestsIdle()
    await Promise.all((client.depsOptimizer?.metadata.depInfoList ?? []).map(dep => dep.processing))
    await server.transformIndexHtml('/', readFileSync(resolve(root, 'index.html'), 'utf8'))
    await client.waitForRequestsIdle()
    ready = true
    return server
  } catch (error) {
    await server.close()
    throw error
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { values } = parseArgs({ options: {
    host: { type: 'string' }, port: { type: 'string' }, config: { type: 'string' },
    strictPort: { type: 'boolean' }, force: { type: 'boolean' },
  } })
  try {
    console.log('正在准备开发模式依赖和页面模块 ...')
    const server = await startFrontendDev({
      host: values.host, port: values.port ? Number(values.port) : undefined,
      configFile: values.config, force: values.force,
    })
    console.log('开发模式前端已就绪。')
    server.printUrls()
    server.bindCLIShortcuts({ print: true })
  } catch (error) {
    console.error('开发模式前端启动失败：', error.message)
    process.exitCode = 1
  }
}
