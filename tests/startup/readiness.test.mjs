import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { createServer } from 'node:http'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

const quote = value => `'${value.replaceAll("'", "''")}'`
const rootScript = fileURLToPath(new URL('../../start.ps1', import.meta.url))
const probeScript = fileURLToPath(new URL('../../tools/wait_for_endpoint.ps1', import.meta.url))

function runProbe(shell, uri, timeoutSeconds = 10) {
  const command = `
    $ErrorActionPreference = 'Stop'
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
    $startupAst = [Management.Automation.Language.Parser]::ParseFile(${quote(rootScript)}, [ref]$null, [ref]$null)
    $assertion = $startupAst.Find({param($node)
      $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-ProcessRunning'
    }, $true)
    Invoke-Expression $assertion.Extent.Text
    . ${quote(probeScript)}
    $currentProcess = [Diagnostics.Process]::GetCurrentProcess()
    Wait-ForEndpoint -Uri ${quote(uri)} -Stage 'Test readiness' -BackendProcess $currentProcess -FrontendProcess $currentProcess -TimeoutSeconds ${timeoutSeconds}
  `
  return new Promise((resolve, reject) => {
    // Execute this repository's fixture in the test child, independent of the user's policy.
    const child = spawn(shell, ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', command], {
      windowsHide: true,
      env: { ...process.env, HTTP_PROXY: 'http://127.0.0.1:1', NO_PROXY: '' },
    })
    let output = ''
    child.stdout.on('data', data => { output += data.toString() })
    child.stderr.on('data', data => { output += data.toString() })
    const timer = setTimeout(() => { child.kill(); reject(new Error(`Probe hung: ${output}`)) }, 15000)
    child.once('error', error => { clearTimeout(timer); reject(error) })
    child.once('close', code => { clearTimeout(timer); resolve({ code, output }) })
  })
}

test('local readiness retries errors, bypasses proxies and bounds stalled response bodies', {
  skip: process.platform !== 'win32', timeout: 60000,
}, async t => {
  let requests = 0
  const server = createServer((request, response) => {
    if (request.url === '/stalled') {
      response.writeHead(200)
      response.write('partial body')
      return
    }
    requests++
    response.writeHead(requests === 1 ? 503 : 200)
    response.end('{}')
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  t.after(() => { server.closeAllConnections(); server.close() })
  const url = `http://127.0.0.1:${server.address().port}`
  for (const shell of ['powershell.exe', 'pwsh.exe']) {
    await t.test(shell, async () => {
      requests = 0
      const ready = await runProbe(shell, `${url}/ready`)
      assert.equal(ready.code, 0, ready.output)
      assert.equal(requests, 2)
      assert.match(ready.output, /Test readiness/)
      const started = Date.now()
      const stalled = await runProbe(shell, `${url}/stalled`, 1)
      assert.notEqual(stalled.code, 0, stalled.output)
      assert.match(stalled.output, /stalled/)
      assert.match(stalled.output, /本次检查超过 2 秒/)
      assert.ok(Date.now() - started < 10000, stalled.output)
    })
  }
})
