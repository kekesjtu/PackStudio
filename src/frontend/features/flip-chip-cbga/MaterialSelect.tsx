import { Box, FormControl, InputLabel, MenuItem, Select, Stack } from '@mui/material'

import type { Material } from './types'

interface MaterialSelectProps {
  label: string
  value: Material
  materials: Material[]
  onChange: (material: Material) => void
}

export default function MaterialSelect({
  label,
  value,
  materials,
  onChange,
}: MaterialSelectProps) {
  return (
    <FormControl size="small" fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select
        label={label}
        value={value.id}
        onChange={(event) => {
          const material = materials.find((item) => item.id === event.target.value)
          if (material !== undefined) onChange(material)
        }}
        renderValue={(materialId) => {
          const material = materials.find((item) => item.id === materialId) ?? value
          return <MaterialOption material={material} />
        }}
      >
        {materials.map((material) => (
          <MenuItem key={material.id} value={material.id}>
            <MaterialOption material={material} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}

function MaterialOption({ material }: { material: Material }) {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Box className="material-swatch" sx={{ backgroundColor: material.color }} />
      <span>{material.name}</span>
    </Stack>
  )
}
