import { Box, FormControlLabel, Stack, Switch, Typography } from '@mui/material'

import MaterialSelect from '../MaterialSelect'
import NumberInput from '../NumberInput'
import type { FlipChipCbgaParameters, Material } from '../types'

interface EncapsulantPropertiesProps {
  parameters: FlipChipCbgaParameters
  materials: Material[]
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function EncapsulantProperties({
  parameters,
  materials,
  onChange,
}: EncapsulantPropertiesProps) {
  const value = parameters.encapsulant
  const update = (patch: Partial<typeof value>) =>
    onChange({ ...parameters, encapsulant: { ...value, ...patch } })
  const derivedHeight =
    parameters.flip_chip_bumps.height + parameters.die.thickness + value.cover_thickness

  return (
    <Stack spacing={2}>
      <FormControlLabel
        control={
          <Switch
            checked={value.enabled}
            onChange={(event) => update({ enabled: event.target.checked })}
          />
        }
        label="包含塑封"
      />
      <Box className="field-grid field-grid-2">
        <NumberInput
          label="塑封长度"
          value={value.length}
          unit="mm"
          onChange={(length) => update({ length: length ?? 0 })}
        />
        <NumberInput
          label="塑封宽度"
          value={value.width}
          unit="mm"
          onChange={(width) => update({ width: width ?? 0 })}
        />
        <NumberInput
          label="芯片顶部覆盖厚度"
          value={value.cover_thickness}
          unit="mm"
          onChange={(cover_thickness) => update({ cover_thickness: cover_thickness ?? 0 })}
        />
      </Box>
      <MaterialSelect
        label="塑封材料"
        value={value.material}
        materials={materials}
        onChange={(material) => update({ material })}
      />
      <Typography variant="body2" color="text.secondary">
        塑封总高度：{derivedHeight.toFixed(3)} mm，顶部盖层完整覆盖芯片。
      </Typography>
    </Stack>
  )
}
