import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'

import type { TemplateRequest } from './types'

interface SpecialFieldsProps {
  request: TemplateRequest
  onChange: (value: TemplateRequest) => void
}

export function SummaryFields({ request, onChange }: SpecialFieldsProps) {
  return (
    <Stack spacing={2}>
      <TextField
        size="small"
        label="设计名称"
        value={request.design_name ?? ''}
        onChange={(event) => onChange({ ...request, design_name: event.target.value })}
      />
    </Stack>
  )
}

export function ModelingFields({ request, onChange }: SpecialFieldsProps) {
  return (
    <Stack spacing={2}>
      {request.bga && (
        <TextField
          select
          size="small"
          label="BGA 焊球阵列建模"
          value={request.bga.representation}
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
      )}
      <TextField
        select
        size="small"
        label="最大网格尺寸预设"
        value={request.mesh.resolution}
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
    </Stack>
  )
}
