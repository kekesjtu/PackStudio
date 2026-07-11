import { Box, FormControl, InputLabel, MenuItem, Select, Stack } from '@mui/material'

import MaterialSelect from '../MaterialSelect'
import NumberInput from '../NumberInput'
import type {
  ArrayLayerParameters,
  ArrayPattern,
  FlipChipCbgaParameters,
  Material,
} from '../types'

interface ArrayGeometryPropertiesProps {
  target: 'flip_chip_bumps' | 'solder_balls'
  parameters: FlipChipCbgaParameters
  materials: Material[]
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function ArrayGeometryProperties({
  target,
  parameters,
  materials,
  onChange,
}: ArrayGeometryPropertiesProps) {
  const value = parameters[target]
  const update = (patch: Partial<ArrayLayerParameters>) =>
    onChange({ ...parameters, [target]: { ...value, ...patch } })
  const isBump = target === 'flip_chip_bumps'

  return (
    <Stack spacing={2}>
      <Box className="field-grid field-grid-2">
        <NumberInput
          label="行数"
          value={value.rows}
          integer
          onChange={(rows) => update({ rows: rows ?? 0 })}
        />
        <NumberInput
          label="列数"
          value={value.columns}
          integer
          onChange={(columns) => update({ columns: columns ?? 0 })}
        />
        <NumberInput
          label="X pitch"
          value={value.pitch_x}
          unit="mm"
          onChange={(pitch_x) => update({ pitch_x: pitch_x ?? 0 })}
        />
        <NumberInput
          label="Y pitch"
          value={value.pitch_y}
          unit="mm"
          onChange={(pitch_y) => update({ pitch_y: pitch_y ?? 0 })}
        />
        <NumberInput
          label="直径"
          value={value.diameter}
          unit="mm"
          onChange={(diameter) => update({ diameter: diameter ?? 0 })}
        />
        <NumberInput
          label="层高"
          value={value.height}
          unit="mm"
          onChange={(height) => update({ height: height ?? 0 })}
        />
      </Box>
      {isBump && (
        <FormControl size="small" fullWidth>
          <InputLabel>凸块排列</InputLabel>
          <Select
            label="凸块排列"
            value={value.pattern}
            onChange={(event) => update({ pattern: event.target.value as ArrayPattern })}
          >
            <MenuItem value="full">全阵列</MenuItem>
            <MenuItem value="staggered">交错阵列</MenuItem>
          </Select>
        </FormControl>
      )}
      <MaterialSelect
        label={isBump ? '凸块材料' : '焊球材料'}
        value={value.element_material}
        materials={materials}
        onChange={(element_material) => update({ element_material })}
      />
      <MaterialSelect
        label={isBump ? 'Underfill 材料' : '焊球层基体材料'}
        value={value.matrix_material}
        materials={materials}
        onChange={(matrix_material) => update({ matrix_material })}
      />
    </Stack>
  )
}
