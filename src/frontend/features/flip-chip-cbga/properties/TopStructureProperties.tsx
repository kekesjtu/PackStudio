import { Box, FormControlLabel, Stack, Switch } from '@mui/material'

import MaterialSelect from '../MaterialSelect'
import NumberInput from '../NumberInput'
import type {
  FlipChipCbgaParameters,
  HeatSlugParameters,
  LidParameters,
  Material,
} from '../types'

interface TopStructurePropertiesProps {
  target: 'lid' | 'heat_slug'
  parameters: FlipChipCbgaParameters
  materials: Material[]
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function TopStructureProperties({
  target,
  parameters,
  materials,
  onChange,
}: TopStructurePropertiesProps) {
  const value = parameters[target]
  const update = (patch: Partial<LidParameters | HeatSlugParameters>) =>
    onChange({ ...parameters, [target]: { ...value, ...patch } })
  const isLid = target === 'lid'
  const structureName = isLid ? '顶盖' : '插入式散热块'

  return (
    <Stack spacing={2}>
      <FormControlLabel
        control={
          <Switch
            checked={value.enabled}
            onChange={(event) => update({ enabled: event.target.checked })}
          />
        }
        label={`包含${structureName}`}
      />
      <Box className="field-grid field-grid-2">
        <NumberInput
          label={`${structureName}长度`}
          value={value.length}
          unit="mm"
          onChange={(length) => update({ length: length ?? 0 })}
        />
        <NumberInput
          label={`${structureName}宽度`}
          value={value.width}
          unit="mm"
          onChange={(width) => update({ width: width ?? 0 })}
        />
        <NumberInput
          label={`${structureName}厚度`}
          value={value.thickness}
          unit="mm"
          onChange={(thickness) => update({ thickness: thickness ?? 0 })}
        />
        <NumberInput
          label="界面层厚度"
          value={value.interface_thickness}
          unit="mm"
          onChange={(interface_thickness) =>
            update({ interface_thickness: interface_thickness ?? 0 })
          }
        />
      </Box>
      <MaterialSelect
        label={`${structureName}材料`}
        value={value.material}
        materials={materials}
        onChange={(material) => update({ material })}
      />
      <MaterialSelect
        label={`${structureName}界面材料`}
        value={value.interface_material}
        materials={materials}
        onChange={(interface_material) => update({ interface_material })}
      />
    </Stack>
  )
}
