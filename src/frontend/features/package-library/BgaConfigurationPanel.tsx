import Alert from '@mui/material/Alert'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'

import NumberInput from '../model-editor/NumberInput'
import FieldShell from '../../ui/FieldShell'
import type { BgaConfiguration } from './types'

interface BgaConfigurationPanelProps {
  value: BgaConfiguration
  section: 'removal' | 'center'
  onChange: (value: BgaConfiguration) => void
}

export default function BgaConfigurationPanel({
  value,
  section,
  onChange,
}: BgaConfigurationPanelProps) {
  const update = (patch: Partial<BgaConfiguration>) => onChange({ ...value, ...patch })
  if (section === 'center') {
    return (
      <Stack spacing={1.5}>
        <FormControlLabel
          className="field-switch"
          control={
            <Switch
              checked={value.center_solder_enabled}
              onChange={(event) => update({ center_solder_enabled: event.target.checked })}
            />
          }
          label="中央焊球"
        />
        {value.center_solder_enabled && (
          <Stack direction="row" spacing={1}>
            <NumberInput
              label="中央行数"
              value={value.center_solder_rows}
              integer
              onChange={(center_solder_rows) =>
                update({ center_solder_rows: center_solder_rows ?? 1 })
              }
            />
            <NumberInput
              label="中央列数"
              value={value.center_solder_columns}
              integer
              onChange={(center_solder_columns) =>
                update({ center_solder_columns: center_solder_columns ?? 1 })
              }
            />
          </Stack>
        )}
      </Stack>
    )
  }
  return (
    <Stack spacing={1.5}>
      <Alert severity="info">
        焊球默认按完整正交阵列生成；去球区域与显式去球单元可以组合，显式去球优先。
        去球区行列同时设为 0 时，仅应用显式去球单元。
      </Alert>
      <FormControlLabel
        className="field-switch"
        control={
          <Switch
            checked={value.solder_removal_enabled}
            onChange={(event) => update({
              solder_removal_enabled: event.target.checked,
              ...(!event.target.checked ? { omitted_cells: [] } : {}),
            })}
          />
        }
        label="焊球去除"
      />
      {value.solder_removal_enabled && (
        <Stack direction="row" spacing={1}>
          <NumberInput
            label="去球区行数"
            value={value.removal_rows}
            integer
            onChange={(removal_rows) => update({ removal_rows: removal_rows ?? 1 })}
          />
          <NumberInput
            label="去球区列数"
            value={value.removal_columns}
            integer
            onChange={(removal_columns) => update({ removal_columns: removal_columns ?? 1 })}
          />
        </Stack>
      )}
      <FieldShell
        label="显式去球单元"
        hint="使用从 0 开始的 行,列；多个单元用分号分隔。"
        disabled={!value.solder_removal_enabled}
      >
        <TextField
          size="small"
          placeholder="例如 0,0; 2,3"
          value={formatCells(value.omitted_cells)}
          disabled={!value.solder_removal_enabled}
          slotProps={{ htmlInput: { 'aria-label': '显式去球单元' } }}
          onChange={(event) => update({ omitted_cells: parseCells(event.target.value) })}
        />
      </FieldShell>
    </Stack>
  )
}

const formatCells = (cells: BgaConfiguration['omitted_cells']) =>
  cells.map((cell) => `${cell.row},${cell.column}`).join('; ')

function parseCells(value: string): BgaConfiguration['omitted_cells'] {
  return value
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => item.split(',').map((part) => Number(part.trim())))
    .filter(
      (parts) =>
        parts.length === 2 &&
        parts.every((part) => Number.isInteger(part) && part >= 0),
    )
    .map(([row, column]) => ({ row, column }))
}
