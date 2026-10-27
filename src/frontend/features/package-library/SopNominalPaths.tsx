import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import FieldShell from '../../ui/FieldShell'
import type { TemplateRequest, WizardField } from './types'
import { valueFor } from './wizardValues'

export default function SopNominalPaths({ request, fields }: {
  request: TemplateRequest; fields: WizardField[]
}) {
  const read = (key: string) => {
    const field = fields.find((f) => f.property_name === key)
    const value = field ? valueFor(field, request, fields) : null
    return typeof value === 'number' ? value : NaN
  }
  const height = read('die.thickness') + read('die.attach') + read('flag.thickness')
    - read('leads.thickness') - read('flag.downset')
  return <Stack spacing={1.5}>
    {(['x', 'y'] as const).map((axis) => {
      const dim = axis === 'x' ? 'length' : 'width'
      const label = axis === 'x' ? '左右名义路径长度' : '上下名义路径长度'
      const length = (read(`flag.${dim}`) - read(`die.${dim}`)) / 2
        + read('leads.gap') + Math.abs(height)
      return <FieldShell key={axis} label={`${label} (mm)`}
        hint="水平跨度与实际端点高差组成的直角路径">
        <TextField size="small" value={Number.isFinite(length) ? Number(length.toFixed(9)) : ''}
          slotProps={{ input: { readOnly: true }, htmlInput: { 'aria-label': label } }} />
      </FieldShell>
    })}
  </Stack>
}
