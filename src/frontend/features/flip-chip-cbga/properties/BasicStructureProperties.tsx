import { Box, Stack } from '@mui/material'

import MaterialSelect from '../MaterialSelect'
import NumberInput from '../NumberInput'
import type { FlipChipCbgaParameters, Material } from '../types'

interface BasicStructurePropertiesProps {
  target: 'substrate' | 'die'
  parameters: FlipChipCbgaParameters
  materials: Material[]
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function BasicStructureProperties({
  target,
  parameters,
  materials,
  onChange,
}: BasicStructurePropertiesProps) {
  if (target === 'substrate') {
    const value = parameters.substrate
    const update = (patch: Partial<typeof value>) =>
      onChange({ ...parameters, substrate: { ...value, ...patch } })
    return (
      <Stack spacing={2}>
        <Box className="field-grid field-grid-2">
          <NumberInput
            label="长度 D"
            value={value.length}
            unit="mm"
            onChange={(length) => update({ length: length ?? 0 })}
          />
          <NumberInput
            label="宽度 E"
            value={value.width}
            unit="mm"
            onChange={(width) => update({ width: width ?? 0 })}
          />
          <NumberInput
            label="厚度 A2"
            value={value.thickness}
            unit="mm"
            onChange={(thickness) => update({ thickness: thickness ?? 0 })}
          />
        </Box>
        <MaterialSelect
          label="基板材料"
          value={value.material}
          materials={materials}
          onChange={(material) => update({ material })}
        />
      </Stack>
    )
  }

  const value = parameters.die
  const update = (patch: Partial<typeof value>) => {
    const die = { ...value, ...patch }
    onChange({
      ...parameters,
      die,
      flip_chip_bumps: {
        ...parameters.flip_chip_bumps,
        footprint_x_override: die.length,
        footprint_y_override: die.width,
      },
    })
  }
  return (
    <Stack spacing={2}>
      <Box className="field-grid field-grid-2">
        <NumberInput
          label="芯片长度"
          value={value.length}
          unit="mm"
          onChange={(length) => update({ length: length ?? 0 })}
        />
        <NumberInput
          label="芯片宽度"
          value={value.width}
          unit="mm"
          onChange={(width) => update({ width: width ?? 0 })}
        />
        <NumberInput
          label="芯片厚度"
          value={value.thickness}
          unit="mm"
          onChange={(thickness) => update({ thickness: thickness ?? 0 })}
        />
        <NumberInput
          label="总功率"
          value={value.power_w}
          unit="W"
          onChange={(power_w) => update({ power_w: power_w ?? 0 })}
        />
      </Box>
      <MaterialSelect
        label="芯片材料"
        value={value.material}
        materials={materials}
        onChange={(material) => update({ material })}
      />
    </Stack>
  )
}
