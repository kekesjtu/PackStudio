import { Alert, Stack } from '@mui/material'

import NumberInput from '../NumberInput'
import type { FlipChipCbgaParameters } from '../types'

interface BoundaryPropertiesProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function BoundaryProperties({
  parameters,
  onChange,
}: BoundaryPropertiesProps) {
  const value = parameters.environment
  const update = (patch: Partial<typeof value>) =>
    onChange({ ...parameters, environment: { ...value, ...patch } })

  return (
    <Stack spacing={2}>
      <NumberInput
        label="环境温度"
        value={value.ambient_temperature_k}
        unit="K"
        onChange={(ambient_temperature_k) =>
          update({ ambient_temperature_k: ambient_temperature_k ?? 0 })
        }
      />
      <NumberInput
        label="默认外表面对流换热系数"
        value={value.default_convection_coefficient_w_m2k}
        unit="W/(m²·K)"
        onChange={(default_convection_coefficient_w_m2k) =>
          update({
            default_convection_coefficient_w_m2k:
              default_convection_coefficient_w_m2k ?? 0,
          })
        }
      />
      <NumberInput
        label="PCB 侧对流换热系数"
        value={value.pcb_convection_coefficient_w_m2k}
        unit="W/(m²·K)"
        onChange={(pcb_convection_coefficient_w_m2k) =>
          update({ pcb_convection_coefficient_w_m2k: pcb_convection_coefficient_w_m2k ?? 0 })
        }
      />
      <NumberInput
        label="顶部对流换热系数"
        value={value.top_convection_coefficient_w_m2k}
        unit="W/(m²·K)"
        onChange={(top_convection_coefficient_w_m2k) =>
          update({ top_convection_coefficient_w_m2k: top_convection_coefficient_w_m2k ?? 0 })
        }
      />
      <Alert severity="warning" icon={false}>
        PCB 侧 1600 W/(m²·K) 是无 PCB 几何时的工程初值；正式结果需按实际板级条件校准。
      </Alert>
    </Stack>
  )
}
