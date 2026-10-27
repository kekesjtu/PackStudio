import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'

import FieldShell from '../../ui/FieldShell'
import NumberInput from '../model-editor/NumberInput'
import type { TemplateRequest } from './types'

interface SpecialFieldsProps {
  request: TemplateRequest
  onChange: (value: TemplateRequest) => void
}

export function SummaryFields({ request, onChange }: SpecialFieldsProps) {
  return (
    <Stack spacing={1.5}>
      <FieldShell label="设计名称">
        <TextField
          size="small"
          value={request.design_name ?? ''}
          slotProps={{ htmlInput: { 'aria-label': '设计名称' } }}
          onChange={(event) => onChange({ ...request, design_name: event.target.value })}
        />
      </FieldShell>
      {(['part_number', 'vendor', 'max_power_w', 'max_junction_temperature_c', 'max_case_temperature_c', 'notes'] as const).map((key) => {
        const label = { part_number: '器件型号', vendor: '厂商名称', max_power_w: '最大额定功率',
          max_junction_temperature_c: '最高工作结温', max_case_temperature_c: '最高壳温', notes: '备注' }[key]
        const numeric = key.startsWith('max_')
        const value = request.summary?.[key]
        if (numeric) return <NumberInput key={key} label={label} allowEmpty
          unit={key === 'max_power_w' ? 'W' : '°C'} value={typeof value === 'number' ? value : null}
          onChange={(value) => onChange({ ...request, summary: { ...request.summary, [key]: value } })} />
        return <FieldShell key={key} label={label}><TextField size="small"
          multiline={key === 'notes'}
          value={request.summary?.[key] ?? ''} slotProps={{ htmlInput: { 'aria-label': label } }}
          onChange={(e) => onChange({ ...request, summary: { ...request.summary,
            [key]: e.target.value } })} />
        </FieldShell>
      })}
    </Stack>
  )
}

export function ModelingFields({ request, onChange }: SpecialFieldsProps) {
  return (
    <Stack spacing={1.5}>
      {request.bga && (
        <FieldShell label="BGA 焊球阵列建模">
          <TextField
            select
            size="small"
            value={request.bga.representation}
            slotProps={{ select: { SelectDisplayProps: { 'aria-label': 'BGA 焊球阵列建模' } } }}
            onChange={(event) =>
              onChange({
                ...request,
                bga: request.bga && {
                  ...request.bga,
                  representation: event.target.value as NonNullable<
                    TemplateRequest['bga']
                  >['representation'],
                },
              })
            }
          >
            <MenuItem value="equivalent" disabled={['chip_array', 'pbga_fc', 'cbga_fc', 'pbga_wb'].includes(request.template_id)
              && (request.bga.ball_map_enabled || request.bga.omitted_cells.length > 0)}>正交各向异性等效层</MenuItem>
            <MenuItem value="discrete">离散建模</MenuItem>
          </TextField>
        </FieldShell>
      )}
    </Stack>
  )
}
