// PackStudio 桌面壳主进程。
//
// 职责：保证本地 FastAPI 后端可用（复用已运行实例或拉起后端子进程），
// 然后打开加载后端端口的窗口。渲染层与 API 同源，无需 CORS 与代理。
const { app, BrowserWindow } = require('electron')
const { spawn } = require('node:child_process')
const { existsSync } = require('node:fs')
const net = require('node:net')
const os = require('node:os')
const path = require('node:path')

const DEFAULT_PORT = 8000
const HEALTH_PATH = '/api/health'
const READY_TIMEOUT_MS = 30_000
const READY_POLL_MS = 250

let backendProcess = null
let mainWindow = null
let quitting = false

// ---- 后端可用性 ----------------------------------------------------------

function isBackendReady(port) {
  return fetch(`http://127.0.0.1:${port}${HEALTH_PATH}`)
    .then((response) => response.ok)
    .catch(() => false)
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address()
      server.close(() => resolve(port))
    })
  })
}

async function waitForBackend(port) {
  const deadline = Date.now() + READY_TIMEOUT_MS
  while (Date.now() < deadline) {
    if (await isBackendReady(port)) return
    await new Promise((resolve) => setTimeout(resolve, READY_POLL_MS))
  }
  throw new Error(`PackStudio 后端未在 ${READY_TIMEOUT_MS}ms 内就绪（端口 ${port}）`)
}

// ---- 后端子进程 ----------------------------------------------------------

// 开发版后端解释器：优先 PACKSTUDIO_PYTHON，其次 PackStudio conda 环境，
// 最后退回 PATH 上的 python（要求已激活包含 packstudio 的环境）。
function resolvePython() {
  if (process.env.PACKSTUDIO_PYTHON) return process.env.PACKSTUDIO_PYTHON
  const pythonName = process.platform === 'win32' ? 'python.exe' : 'python'
  const condaCandidate = path.join(os.homedir(), '.conda', 'envs', 'PackStudio', pythonName)
  if (existsSync(condaCandidate)) return condaCandidate
  return 'python'
}

function startBackend(port) {
  if (app.isPackaged) {
    // 打包版：resources/backend 下的 PyInstaller 独立可执行文件，
    // 前端产物在 resources/frontend，通过环境变量交给后端托管
    const executable = path.join(process.resourcesPath, 'backend', 'packstudio-backend.exe')
    backendProcess = spawn(executable, ['--port', String(port)], {
      env: {
        ...process.env,
        PACKSTUDIO_FRONTEND_DIR: path.join(process.resourcesPath, 'frontend'),
      },
      stdio: 'ignore',
      windowsHide: true,
    })
  } else {
    // 开发版：仓库根目录运行 python -m packstudio，可用 PACKSTUDIO_PYTHON 指定解释器
    backendProcess = spawn(
      resolvePython(),
      ['-m', 'packstudio', '--port', String(port)],
      { cwd: path.join(__dirname, '..'), stdio: 'pipe', windowsHide: true },
    )
    backendProcess.stdout?.on('data', (chunk) => process.stdout.write(chunk))
    backendProcess.stderr?.on('data', (chunk) => process.stderr.write(chunk))
  }
  backendProcess.on('error', (error) => {
    console.error('无法启动 PackStudio 后端：', error.message)
    if (!quitting) app.exit(1)
  })
  backendProcess.on('exit', (code) => {
    console.error(`PackStudio 后端已退出（code=${code}）`)
    if (!quitting && mainWindow) {
      app.exit(1)
    }
  })
}

async function resolvePort() {
  if (await isBackendReady(DEFAULT_PORT)) return DEFAULT_PORT
  const port = await findFreePort()
  startBackend(port)
  try {
    await waitForBackend(port)
  } catch (error) {
    if (backendProcess && !backendProcess.killed) backendProcess.kill()
    throw error
  }
  return port
}

// ---- 窗口 ----------------------------------------------------------------

function createWindow(url) {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  })
  mainWindow.loadURL(url)
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ---- 生命周期 ------------------------------------------------------------

app.whenReady().then(async () => {
  try {
    const port = await resolvePort()
    createWindow(`http://127.0.0.1:${port}`)
  } catch (error) {
    console.error('启动失败：', error.message)
    app.exit(1)
  }
})

app.on('window-all-closed', () => {
  app.quit()
})

app.on('will-quit', () => {
  quitting = true
  if (backendProcess && !backendProcess.killed) backendProcess.kill()
})
