import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import ts from 'typescript'

export default function frontendDependencies(directory: string): string[] {
  const dependencies = new Set(['react-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'])
  for (const file of readdirSync(directory, { recursive: true })) {
    if (typeof file !== 'string' || !/\.tsx?$/.test(file)) continue
    const source = readFileSync(join(directory, file), 'utf8')
    for (const { fileName } of ts.preProcessFile(source, true).importedFiles) {
      if (!fileName.startsWith('.') && !fileName.startsWith('/')) dependencies.add(fileName)
    }
  }
  return [...dependencies].sort()
}
