import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import FieldShell from '../../ui/FieldShell'
import numericInput from '../../ui/numericInput'
import NumericUnit from '../../ui/NumericUnit'

interface Row { depth: number | null; thickness: number | null; coverage: number | null; disconnect?: boolean }

export default function MetalLayerTable({ label, value, enabled, onChange, outerFaces = false, disconnect = false }: {
  label: string; value: string; enabled: boolean; onChange: (value: string) => void; outerFaces?: boolean; disconnect?: boolean
}) {
  let rows: Row[] = []
  try { rows = JSON.parse(value) as Row[] } catch { /* Backend reports malformed table input. */ }
  const update = (next: Row[]) => onChange(JSON.stringify(next))
  return <FieldShell label={label} hint="深度从整个基板顶面量起，长度单位 mm，覆盖率单位 %" disabled={!enabled}>
    <Stack spacing={1}>
      {rows.map((row, index) => <Stack key={index} direction="row" spacing={0.5}>
        {(['depth', 'thickness', 'coverage'] as const).map((key) => <TextField
          key={key} size="small" type="number"
          disabled={!enabled || (outerFaces && key === 'depth' && (index === 0 || index === rows.length - 1))}
          label={{ depth: 'Depth', thickness: 'Thickness', coverage: 'Coverage' }[key]}
          value={row[key] ?? ''} slotProps={{
            input: { endAdornment: <NumericUnit unit={key === 'coverage' ? '%' : 'mm'} /> },
            htmlInput: {
            'aria-label': `${label} 第 ${index + 1} 行 ${key}`, ...numericInput(),
          } }}
          onChange={(event) => update(rows.map((r, i) => i === index
            ? { ...r, [key]: event.target.value === '' ? null : Number(event.target.value) } : r))}
        />)}
        {disconnect && <FormControlLabel label="Disconnect to Via" control={<Checkbox
          checked={row.disconnect ?? false} disabled={!enabled}
          slotProps={{ input: { 'aria-label': `${label} 第 ${index + 1} 行 disconnect` } }}
          onChange={(event) => update(rows.map((r, i) => i === index
            ? { ...r, disconnect: event.target.checked } : r))} />} />}
        <Button disabled={!enabled} aria-label={`删除第 ${index + 1} 层`}
          onClick={() => update(rows.filter((_, i) => i !== index))}>删除</Button>
      </Stack>)}
      <Button disabled={!enabled || rows.length >= 10} onClick={() => update([
        ...rows, { depth: null, thickness: null, coverage: null },
      ])}>添加金属层</Button>
    </Stack>
  </FieldShell>
}
