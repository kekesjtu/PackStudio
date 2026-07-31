import { MenuItem, Stack, TextField } from '@mui/material'

import NumberInput from '../model-editor/NumberInput'
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

export function BoundaryFields({ request, onChange }: SpecialFieldsProps) {
  const update = (patch: Partial<TemplateRequest['environment']>) =>
    onChange({ ...request, environment: { ...request.environment, ...patch } })
  return (
    <Stack spacing={2}>
      <NumberInput
        label="环境温度"
        unit="K"
        value={request.environment.ambient_temperature_k}
        onChange={(value) => update({ ambient_temperature_k: value ?? 0 })}
      />
      <NumberInput
        label="普通外表面对流"
        unit="W/(m²·K)"
        value={request.environment.default_convection_coefficient_w_m2k}
        onChange={(value) =>
          update({ default_convection_coefficient_w_m2k: value ?? 0 })
        }
      />
      <NumberInput
        label="PCB 侧换热系数"
        unit="W/(m²·K)"
        value={request.environment.pcb_convection_coefficient_w_m2k}
        onChange={(value) => update({ pcb_convection_coefficient_w_m2k: value ?? 0 })}
      />
      <NumberInput
        label="顶部换热系数"
        unit="W/(m²·K)"
        value={request.environment.top_convection_coefficient_w_m2k}
        onChange={(value) => update({ top_convection_coefficient_w_m2k: value ?? 0 })}
      />
    </Stack>
  )
}
