import { FormControl, InputLabel, MenuItem, Select, Stack, Typography } from '@mui/material'

import type { FlipChipCbgaParameters, MeshResolution } from '../types'

interface MeshPropertiesProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

const meshDescriptions: Record<MeshResolution, string> = {
  coarse: 'XY 每层约 12 份，Z 方向 1 份；用于快速检查。',
  standard: 'XY 每层约 24 份，Z 方向 2 份；适合常规稳态仿真。',
  fine: 'XY 每层约 40 份，Z 方向 4 份；用于温度梯度复核。',
}

export default function MeshProperties({ parameters, onChange }: MeshPropertiesProps) {
  const resolution = parameters.mesh.resolution
  return (
    <Stack spacing={2}>
      <FormControl size="small" fullWidth>
        <InputLabel>最大网格尺寸</InputLabel>
        <Select
          label="最大网格尺寸"
          value={resolution}
          onChange={(event) =>
            onChange({
              ...parameters,
              mesh: { resolution: event.target.value as MeshResolution },
            })
          }
        >
          <MenuItem value="coarse">粗</MenuItem>
          <MenuItem value="standard">标准（默认）</MenuItem>
          <MenuItem value="fine">细</MenuItem>
        </Select>
      </FormControl>
      <Typography variant="body2" color="text.secondary">
        {meshDescriptions[resolution]}
      </Typography>
    </Stack>
  )
}
