// @vitest-environment node
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { expect, it } from 'vitest'

import frontendDependencies from '../../src/tooling/frontendDependencies'

it('collects nested static and dynamic package imports without scanning other directories', () => {
  const directory = mkdtempSync(join(tmpdir(), 'packstudio-dependencies-'))
  try {
    mkdirSync(join(directory, 'nested'))
    writeFileSync(join(directory, 'entry.tsx'), `
      import React from 'react'
      import Box from '@mui/material/Box'
      import './styles.css'
      import type { LocalType } from './types'
      const helper = import('dynamic-helper')
    `)
    writeFileSync(join(directory, 'nested/other.ts'), "import Box from '@mui/material/Box'")
    writeFileSync(join(directory, 'ignored.html'), "<script>import 'unrelated-package'</script>")
    expect(frontendDependencies(directory)).toEqual([
      '@mui/material/Box', 'dynamic-helper', 'react', 'react-dom',
      'react/jsx-dev-runtime', 'react/jsx-runtime',
    ])
  } finally {
    expect(dirname(directory)).toBe(resolve(tmpdir()))
    expect(basename(directory)).toMatch(/^packstudio-dependencies-/)
    rmSync(directory, { recursive: true, force: true })
  }
})
