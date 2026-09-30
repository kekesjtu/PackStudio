const assert = require('node:assert/strict')
const { EventEmitter } = require('node:events')
const Module = require('node:module')
const { setTimeout: delay } = require('node:timers/promises')
const { test } = require('node:test')

test('Electron starts a real uv backend and closes its complete process tree', async () => {
  const nativeFetch = globalThis.fetch
  const originalLoad = Module._load
  const app = new EventEmitter()
  app.isPackaged = false
  app.whenReady = () => Promise.resolve()
  app.quit = () => app.emit('will-quit')
  let resolveUrl
  let rejectUrl
  const openedUrl = new Promise((resolve, reject) => {
    resolveUrl = resolve
    rejectUrl = reject
  })
  app.exit = (code) => rejectUrl(new Error(`desktop exited with ${code}`))
  class BrowserWindow {
    loadURL(url) { resolveUrl(url) }
    on() {}
  }
  // Skip a possibly user-owned instance on the default port; exercise the
  // managed backend on the real free port chosen by the desktop lifecycle.
  globalThis.fetch = (url, ...args) => String(url).includes('127.0.0.1:8000/')
    ? Promise.reject(new Error('isolated desktop test')) : nativeFetch(url, ...args)
  Module._load = function (id, parent, isMain) {
    if (id === 'electron') return { app, BrowserWindow }
    return originalLoad.call(this, id, parent, isMain)
  }
  let backendUrl
  try {
    require('../../electron/main.cjs')
    backendUrl = await Promise.race([
      openedUrl,
      delay(35000, undefined, { ref: false }).then(() => { throw new Error('startup timed out') }),
    ])
    const response = await nativeFetch(`${backendUrl}/api/health`)
    assert.equal(response.status, 200)
    assert.equal((await response.json()).service, 'packstudio')
    app.emit('will-quit')
    let stopped = false
    for (let attempt = 0; attempt < 20; attempt++) {
      try { await nativeFetch(`${backendUrl}/api/health`) } catch { stopped = true; break }
      await delay(100)
    }
    assert.equal(stopped, true, 'uv child backend must not outlive Electron shutdown')
  } finally {
    app.emit('will-quit')
    globalThis.fetch = nativeFetch
    Module._load = originalLoad
  }
})
