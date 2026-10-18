import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'

import FieldShell from '../../ui/FieldShell'
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
            <MenuItem value="equivalent">正交各向异性等效层</MenuItem>
            <MenuItem value="discrete">离散建模</MenuItem>
          </TextField>
        </FieldShell>
      )}
      <FieldShell label="最大网格尺寸预设">
        <TextField
          select
          size="small"
          value={request.mesh.resolution}
          slotProps={{ select: { SelectDisplayProps: { 'aria-label': '最大网格尺寸预设' } } }}
          onChange={(event) =>
            onChange({
              ...request,
              mesh: {
                resolution: event.target.value as TemplateRequest['mesh']['resolution'],
              },
            })
          }
        >
          <MenuItem value="coarse">粗</MenuItem>
          <MenuItem value="standard">标准</MenuItem>
          <MenuItem value="fine">细</MenuItem>
        </TextField>
      </FieldShell>
    </Stack>
  )
}
