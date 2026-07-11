import { Box, Paper, Typography } from '@mui/material'

import NumberInput from './NumberInput'
import type { EnvironmentParameters } from './types'

interface EnvironmentSectionProps {
  value: EnvironmentParameters
  onChange: (value: EnvironmentParameters) => void
}

export default function EnvironmentSection({ value, onChange }: EnvironmentSectionProps) {
  const update = (patch: Partial<EnvironmentParameters>) => onChange({ ...value, ...patch })

  return (
    <Paper variant="outlined" className="parameter-section">
      <Typography variant="h6" component="h3">
        边界条件
      </Typography>
      <Typography variant="body2" color="text.secondary">
        系数留空表示该表面保持默认绝热；PTA XML 只导出已启用的边界。
      </Typography>
      <Box className="field-grid field-grid-3">
        <NumberInput
          label="环境温度"
          value={value.ambient_temperature_k}
          unit="K"
          onChange={(ambient_temperature_k) =>
            update({ ambient_temperature_k: ambient_temperature_k ?? 0 })
          }
        />
        <NumberInput
          label="底面对流系数"
          value={value.bottom_convection_coefficient_w_m2k}
          unit="W/(m²·K)"
          allowEmpty
          onChange={(bottom_convection_coefficient_w_m2k) =>
            update({ bottom_convection_coefficient_w_m2k })
          }
        />
        <NumberInput
          label="顶面对流系数"
          value={value.top_convection_coefficient_w_m2k}
          unit="W/(m²·K)"
          allowEmpty
          onChange={(top_convection_coefficient_w_m2k) =>
            update({ top_convection_coefficient_w_m2k })
          }
        />
      </Box>
    </Paper>
  )
}
