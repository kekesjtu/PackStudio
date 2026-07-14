import {
  Alert,
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import {
  applyPackagePreset,
  detectPackagePreset,
  packagePresets,
} from '../packagePresets'
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
  const selectedPreset = detectPackagePreset(parameters) ?? 'custom'

  return (
    <Stack spacing={2}>
      <TextField
        label="设计名称"
        size="small"
        value={parameters.design_name}
        onChange={(event) => onChange({ ...parameters, design_name: event.target.value })}
        fullWidth
      />
      <FormControl size="small" fullWidth>
        <InputLabel id="package-preset-label">基本尺寸预设</InputLabel>
        <Select
          labelId="package-preset-label"
          label="基本尺寸预设"
          value={selectedPreset}
          onChange={(event) => onChange(applyPackagePreset(parameters, event.target.value))}
        >
          {selectedPreset === 'custom' && (
            <MenuItem value="custom" disabled>
              自定义尺寸
            </MenuItem>
          )}
          {packagePresets.map((preset) => (
            <MenuItem key={preset.id} value={preset.id}>
              {preset.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Alert severity="warning" icon={false}>
        切换预设会覆盖基板、芯片、凸点、焊球和顶部结构尺寸；如需保留当前配置，请先点击底部“保存参数”。
      </Alert>
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
