import { Box, Stack, TextField, Typography } from '@mui/material'

import type { FlipChipCbgaParameters, PackageModel } from '../types'

interface SummaryPropertiesProps {
  parameters: FlipChipCbgaParameters
  model: PackageModel | null
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function SummaryProperties({
  parameters,
  model,
  onChange,
}: SummaryPropertiesProps) {
  return (
    <Stack spacing={2}>
      <TextField
        label="设计名称"
        size="small"
        value={parameters.design_name}
        onChange={(event) => onChange({ ...parameters, design_name: event.target.value })}
        fullWidth
      />
      <Box className="summary-grid">
        <SummaryValue label="矩形块" value={model?.blocks.length ?? '—'} />
        <SummaryValue label="材料" value={model?.materials.length ?? '—'} />
        <SummaryValue label="物理焊球" value={model?.metadata.solder_ball_count ?? '—'} />
        <SummaryValue label="塑封块" value={model?.metadata.encapsulant_block_count ?? 0} />
      </Box>
    </Stack>
  )
}

function SummaryValue({
  label,
  value,
}: {
  label: string
  value: string | number | boolean
}) {
  return (
    <Box className="summary-value">
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6">{String(value)}</Typography>
    </Box>
  )
}
