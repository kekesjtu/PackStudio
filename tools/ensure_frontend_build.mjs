import { execSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const configFiles = [
  'index.html', 'package.json', 'package-lock.json', 'vite.config.ts',
  'tsconfig.json', 'tsconfig.app.json', 'tsconfig.node.json',
]
const stampName = '.packstudio-build.json'

function filesIn(directory) {
  if (!existsSync(directory)) return []
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    return entry.isDirectory() ? filesIn(path) : entry.isFile() ? [path] : []
  })
}

function fingerprint(root, files) {
  const hash = createHash('sha256').update(process.version)
  for (const path of files.sort()) {
    hash.update(relative(root, path).replaceAll('\\', '/')).update('\0')
    hash.update(readFileSync(path)).update('\0')
  }
  return hash.digest('hex')
}

export function ensureFrontendBuild({
  root = resolve(dirname(fileURLToPath(import.meta.url)), '..'),
  force = false,
  build = () => execSync('npm run build', { cwd: root, stdio: 'inherit' }),
} = {}) {
  const sourceFiles = [
    ...configFiles.map((name) => join(root, name)),
    ...filesIn(join(root, 'src/frontend')),
    ...filesIn(join(root, 'public')),
  ]
  const sourceHash = fingerprint(root, sourceFiles)
  const outputDirectory = join(root, 'dist')
  const stampPath = join(outputDirectory, stampName)
  const outputFiles = () => filesIn(outputDirectory).filter((path) => path !== stampPath)
  let stamp
  try { stamp = JSON.parse(readFileSync(stampPath, 'utf8')) } catch { /* Build on a cache miss. */ }
  if (!force && existsSync(join(outputDirectory, 'index.html')) &&
      stamp?.sourceHash === sourceHash && stamp.outputHash === fingerprint(root, outputFiles())) {
    return false
  }
  build()
  if (!existsSync(join(outputDirectory, 'index.html'))) {
    throw new Error('前端构建没有生成 dist/index.html')
  }
  writeFileSync(stampPath, JSON.stringify({
    sourceHash, outputHash: fingerprint(root, outputFiles()),
  }) + '\n')
  return true
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const rebuilt = ensureFrontendBuild({ force: process.argv.includes('--force') })
  console.log(rebuilt ? '前端生产构建已更新。' : '前端生产构建未变，复用缓存。')
}
