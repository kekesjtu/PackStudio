import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'

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
  const updateBalls = (patch: Partial<FlipChipCbgaParameters['solder_balls']>) =>
    onChange({ ...parameters, solder_balls: { ...parameters.solder_balls, ...patch } })

  return (
    <Stack spacing={2}>
      <Typography variant="subtitle2">阵列表达</Typography>
      <RepresentationSelect
        label="焊球建模方式"
        value={parameters.solder_balls.representation}
        onChange={(representation) => updateBalls({ representation })}
      />
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
