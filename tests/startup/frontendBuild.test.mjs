import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, unlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, dirname, join, resolve } from 'node:path'
import { test } from 'node:test'

import { ensureFrontendBuild } from '../../tools/ensure_frontend_build.mjs'

test('build cache tracks source, public assets, configuration and output integrity', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'packstudio-build-'))
  t.after(() => {
    assert.equal(dirname(root), resolve(tmpdir()))
    assert.ok(basename(root).startsWith('packstudio-build-'))
    rmSync(root, { recursive: true, force: true })
  })
  for (const name of [
    'index.html', 'package.json', 'package-lock.json', 'vite.config.ts',
    'tsconfig.json', 'tsconfig.app.json', 'tsconfig.node.json',
  ]) writeFileSync(join(root, name), '{}')
  mkdirSync(join(root, 'src/frontend'), { recursive: true })
  mkdirSync(join(root, 'public'))
  const source = join(root, 'src/frontend/main.tsx')
  writeFileSync(source, 'original source')
  let builds = 0
  const options = { root, build() {
    builds++
    mkdirSync(join(root, 'dist'), { recursive: true })
    writeFileSync(join(root, 'dist/index.html'), '<script src="/app.js"></script>')
    writeFileSync(join(root, 'dist/app.js'), `build ${builds}`)
  } }
  assert.equal(ensureFrontendBuild(options), true)
  assert.equal(ensureFrontendBuild(options), false)
  assert.equal(builds, 1)
  for (const [path, contents] of [
    [source, 'updated source'],
    [join(root, 'vite.config.ts'), 'updated config'],
    [join(root, 'public/icon.svg'), '<svg/>'],
    [join(root, 'dist/app.js'), 'damaged asset'],
    [join(root, 'dist/.packstudio-build.json'), 'invalid JSON'],
  ]) {
    writeFileSync(path, contents)
    assert.equal(ensureFrontendBuild(options), true)
    assert.equal(ensureFrontendBuild(options), false)
  }
  unlinkSync(join(root, 'dist/app.js'))
  assert.equal(ensureFrontendBuild(options), true)
  assert.equal(ensureFrontendBuild({ ...options, force: true }), true)
  const stamp = readFileSync(join(root, 'dist/.packstudio-build.json'), 'utf8')
  writeFileSync(source, 'cannot build')
  assert.throws(() => ensureFrontendBuild({ root, build() { throw new Error('build failed') } }))
  assert.equal(readFileSync(join(root, 'dist/.packstudio-build.json'), 'utf8'), stamp)
})
