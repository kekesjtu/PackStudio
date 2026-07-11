import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'

import NumberInput from '../NumberInput'
import type {
  ArrayRepresentation,
  FlipChipCbgaParameters,
} from '../types'

interface ModelingOptionsPropertiesProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function ModelingOptionsProperties({
  parameters,
  onChange,
}: ModelingOptionsPropertiesProps) {
  const updateBumps = (patch: Partial<FlipChipCbgaParameters['flip_chip_bumps']>) =>
    onChange({
      ...parameters,
      flip_chip_bumps: { ...parameters.flip_chip_bumps, ...patch },
    })
  const updateBalls = (patch: Partial<FlipChipCbgaParameters['solder_balls']>) =>
    onChange({ ...parameters, solder_balls: { ...parameters.solder_balls, ...patch } })
  const updateEnvironment = (patch: Partial<FlipChipCbgaParameters['environment']>) =>
    onChange({ ...parameters, environment: { ...parameters.environment, ...patch } })

  return (
    <Stack spacing={2}>
      <Typography variant="subtitle2">阵列表达</Typography>
      <RepresentationSelect
        label="凸块建模方式"
        value={parameters.flip_chip_bumps.representation}
        onChange={(representation) => updateBumps({ representation })}
      />
      <RepresentationSelect
        label="焊球建模方式"
        value={parameters.solder_balls.representation}
        onChange={(representation) => updateBalls({ representation })}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={parameters.flip_chip_bumps.emit_matrix_blocks}
            onChange={(event) => updateBumps({ emit_matrix_blocks: event.target.checked })}
          />
        }
        label="离散凸块补齐 Underfill"
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={parameters.solder_balls.emit_matrix_blocks}
            onChange={(event) => updateBalls({ emit_matrix_blocks: event.target.checked })}
          />
        }
        label="离散焊球补齐基体"
      />
      <Typography variant="subtitle2">边界条件</Typography>
      <NumberInput
        label="环境温度"
        value={parameters.environment.ambient_temperature_k}
        unit="K"
        onChange={(ambient_temperature_k) =>
          updateEnvironment({ ambient_temperature_k: ambient_temperature_k ?? 0 })
        }
      />
      <Box className="field-grid field-grid-2">
        <NumberInput
          label="底面对流"
          value={parameters.environment.bottom_convection_coefficient_w_m2k}
          unit="W/(m²·K)"
          allowEmpty
          onChange={(bottom_convection_coefficient_w_m2k) =>
            updateEnvironment({ bottom_convection_coefficient_w_m2k })
          }
        />
        <NumberInput
          label="顶面对流"
          value={parameters.environment.top_convection_coefficient_w_m2k}
          unit="W/(m²·K)"
          allowEmpty
          onChange={(top_convection_coefficient_w_m2k) =>
            updateEnvironment({ top_convection_coefficient_w_m2k })
          }
        />
      </Box>
    </Stack>
  )
}

function RepresentationSelect({
  label,
  value,
  onChange,
}: {
  label: string
  value: ArrayRepresentation
  onChange: (value: ArrayRepresentation) => void
}) {
  return (
    <FormControl size="small" fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select
        label={label}
        value={value}
        onChange={(event) => onChange(event.target.value as ArrayRepresentation)}
      >
        <MenuItem value="equivalent">各向异性等效块</MenuItem>
        <MenuItem value="discrete">离散等体积方柱</MenuItem>
      </Select>
    </FormControl>
  )
}
