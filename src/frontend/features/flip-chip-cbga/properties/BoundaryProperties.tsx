import { Alert, FormControlLabel, Stack, Switch } from '@mui/material'

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
  const topOverride = value.top_to_ambient_thermal_resistance_k_w !== null

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
        label="默认外表面对流系数"
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
        label="PCB→环境等效热阻"
        value={value.board_to_ambient_thermal_resistance_k_w}
        unit="K/W"
        onChange={(board_to_ambient_thermal_resistance_k_w) =>
          update({
            board_to_ambient_thermal_resistance_k_w:
              board_to_ambient_thermal_resistance_k_w ?? 0,
          })
        }
      />
      <FormControlLabel
        control={
          <Switch
            checked={topOverride}
            onChange={(event) =>
              update({ top_to_ambient_thermal_resistance_k_w: event.target.checked ? 10 : null })
            }
          />
        }
        label="设置顶部关键散热面"
      />
      {topOverride && (
        <NumberInput
          label="顶部→环境等效热阻"
          value={value.top_to_ambient_thermal_resistance_k_w}
          unit="K/W"
          onChange={(top_to_ambient_thermal_resistance_k_w) =>
            update({ top_to_ambient_thermal_resistance_k_w })
          }
        />
      )}
      <Alert severity="warning" icon={false}>
        PCB 等效热阻是无 PCB 几何时的工程初值，正式结果需按实际板级条件校准。
      </Alert>
    </Stack>
  )
}
