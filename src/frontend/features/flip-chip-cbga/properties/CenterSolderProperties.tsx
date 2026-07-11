import { Box, FormControlLabel, Stack, Switch, Typography } from '@mui/material'

import NumberInput from '../NumberInput'
import type { ArrayLayerParameters, FlipChipCbgaParameters } from '../types'

interface CenterSolderPropertiesProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function CenterSolderProperties({
  parameters,
  onChange,
}: CenterSolderPropertiesProps) {
  const value = parameters.solder_balls
  const update = (patch: Partial<ArrayLayerParameters>) =>
    onChange({ ...parameters, solder_balls: { ...value, ...patch } })
  const enabled = value.pattern === 'center_populated'

  const setEnabled = (nextEnabled: boolean) => {
    update(
      nextEnabled
        ? {
            pattern: 'center_populated',
            center_rows: value.center_rows || defaultCenterSize(value.rows),
            center_columns: value.center_columns || defaultCenterSize(value.columns),
          }
        : { pattern: 'full' },
    )
  }

  return (
    <Stack spacing={2}>
      <FormControlLabel
        control={<Switch checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />}
        label="使用中央焊球独立分区"
      />
      <Box className="field-grid field-grid-2">
        <NumberInput
          label="中央区域行数"
          value={value.center_rows}
          integer
          onChange={(center_rows) => update({ center_rows: center_rows ?? 0 })}
        />
        <NumberInput
          label="中央区域列数"
          value={value.center_columns}
          integer
          onChange={(center_columns) => update({ center_columns: center_columns ?? 0 })}
        />
      </Box>
      <Typography variant="body2" color="text.secondary">
        启用后，外围均匀区域拆为四块，中央区域作为独立的 Center_SBall 等效块。
      </Typography>
    </Stack>
  )
}

const defaultCenterSize = (total: number) =>
  total < 3 ? 0 : total % 2 === 0 ? 2 : Math.min(3, total - 2)
