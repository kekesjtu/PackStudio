import Alert from '@mui/material/Alert'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'

import NumberInput from '../model-editor/NumberInput'
import SolderRemovalMatrix from './SolderRemovalMatrix'
import type { ViaConfiguration } from './types'

interface ViaRemovalPanelProps {
  value: ViaConfiguration
  enabled: boolean
  rows: number
  columns: number
  onChange: (value: ViaConfiguration) => void
}

export default function ViaRemovalPanel({ value, enabled, rows, columns, onChange }: ViaRemovalPanelProps) {
  const update = (patch: Partial<ViaConfiguration>) => onChange({ ...value, ...patch })
  if (!enabled) return <Alert severity="info">请先在热通孔步骤中启用热通孔。</Alert>
  return (
    <Stack spacing={1.5}>
      <Alert severity="info">
        去孔区与显式去孔可以组合；去孔区行列同时为 0 时，仅应用显式去孔。
        区域居中，奇偶不同向负轴取整。行是 Y 方向，列是 X 方向。
      </Alert>
      <FormControlLabel
        className="field-switch"
        label="热通孔去除"
        control={<Switch checked={value.removal_enabled} onChange={(event) => update({
          removal_enabled: event.target.checked,
          ...(!event.target.checked ? { omitted_cells: [] } : {}),
        })} />}
      />
      {value.removal_enabled && <>
        <Stack direction="row" spacing={1}>
          <NumberInput label="去孔区行数" value={value.removal_rows} integer allowEmpty
            onChange={(removal_rows) => update({ removal_rows })} />
          <NumberInput label="去孔区列数" value={value.removal_columns} integer allowEmpty
            onChange={(removal_columns) => update({ removal_columns })} />
        </Stack>
        {rows > 0 && columns > 0 && <SolderRemovalMatrix kind="via" rows={rows} columns={columns}
          omittedCells={value.omitted_cells} removalRows={value.removal_rows}
          removalColumns={value.removal_columns}
          onChange={(omitted_cells) => update({ omitted_cells })} />}
      </>}
    </Stack>
  )
}
