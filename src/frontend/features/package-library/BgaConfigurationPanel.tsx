import {
  Alert,
  FormControlLabel,
  MenuItem,
  Stack,
  Switch,
  TextField,
} from '@mui/material'

import NumberInput from '../model-editor/NumberInput'
import type { BgaConfiguration } from './types'

interface BgaConfigurationPanelProps {
  value: BgaConfiguration
  onChange: (value: BgaConfiguration) => void
}

export default function BgaConfigurationPanel({
  value,
  onChange,
}: BgaConfigurationPanelProps) {
  const update = (patch: Partial<BgaConfiguration>) => onChange({ ...value, ...patch })
  return (
    <Stack spacing={2}>
      <Alert severity="info">
        默认隐式为正交全阵列。只提供可组合的中央焊球与焊球去除；显式去球优先。
      </Alert>
      <TextField
        select
        size="small"
        label="焊球阵列建模"
        value={value.representation}
        onChange={(event) =>
          update({ representation: event.target.value as BgaConfiguration['representation'] })
        }
      >
        <MenuItem value="equivalent">正交各向异性等效层</MenuItem>
        <MenuItem value="discrete">离散建模</MenuItem>
      </TextField>
      <FormControlLabel
        control={
          <Switch
            checked={value.solder_removal_enabled}
            onChange={(event) => update({ solder_removal_enabled: event.target.checked })}
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
      <FormControlLabel
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
            onChange={(center_solder_rows) => update({ center_solder_rows: center_solder_rows ?? 1 })}
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
      <TextField
        label="显式去球单元"
        size="small"
        placeholder="例如 0,0; 2,3"
        value={formatCells(value.omitted_cells)}
        disabled={!value.solder_removal_enabled}
        helperText="使用从 0 开始的 行,列；多个单元用分号分隔。"
        onChange={(event) => update({ omitted_cells: parseCells(event.target.value) })}
      />
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
