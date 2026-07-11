import { Box, Button, CircularProgress, Stack, Typography } from '@mui/material'

import ArraySection from './ArraySection'
import EnvironmentSection from './EnvironmentSection'
import PackageSection from './PackageSection'
import TopSection from './TopSection'
import type { FlipChipCbgaParameters } from './types'

interface ParameterPanelProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
  onGenerate: () => void
  onExport: () => void
  busy: boolean
  exportDisabled: boolean
}

export default function ParameterPanel({
  parameters,
  onChange,
  onGenerate,
  onExport,
  busy,
  exportDisabled,
}: ParameterPanelProps) {
  return (
    <Box className="parameter-scroll">
      <Box>
        <Typography variant="h5" component="h2">
          封装参数
        </Typography>
        <Typography color="text.secondary">
          所有尺寸使用 mm；修改后重新生成模型并检查右侧几何树。
        </Typography>
      </Box>
      <PackageSection parameters={parameters} onChange={onChange} />
      <ArraySection
        title="Flip-chip 凸块与 Underfill"
        description="圆柱焊点按等体积方柱离散，或使用第 4 节公式生成各向异性等效层。"
        value={parameters.flip_chip_bumps}
        onChange={(flip_chip_bumps) => onChange({ ...parameters, flip_chip_bumps })}
      />
      <ArraySection
        title="BGA 焊球分布"
        description="支持全阵列、交错、中央去球、中央焊球及自定义去球。"
        value={parameters.solder_balls}
        onChange={(solder_balls) => onChange({ ...parameters, solder_balls })}
      />
      <TopSection parameters={parameters} onChange={onChange} />
      <EnvironmentSection
        value={parameters.environment}
        onChange={(environment) => onChange({ ...parameters, environment })}
      />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} className="action-bar">
        <Button variant="contained" onClick={onGenerate} disabled={busy}>
          {busy ? <CircularProgress size={22} color="inherit" /> : '生成模型'}
        </Button>
        <Button variant="outlined" onClick={onExport} disabled={busy || exportDisabled}>
          导出精简 PTA XML
        </Button>
      </Stack>
    </Box>
  )
}
