import Alert from '@mui/material/Alert'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'

import NumberInput from '../model-editor/NumberInput'
import SolderRemovalMatrix from './SolderRemovalMatrix'
import type { BgaConfiguration } from './types'

interface BgaConfigurationPanelProps {
  value: BgaConfiguration
  section: 'removal' | 'center'
  rows: number
  columns: number
  onChange: (value: BgaConfiguration) => void
}

export default function BgaConfigurationPanel({
  value,
  section,
  rows,
  columns,
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
              allowEmpty
              onChange={(center_solder_rows) =>
                update({ center_solder_rows })
              }
            />
            <NumberInput
              label="中央列数"
              value={value.center_solder_columns}
              integer
              allowEmpty
              onChange={(center_solder_columns) =>
                update({ center_solder_columns })
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
        <>
          <Stack direction="row" spacing={1}>
            <NumberInput
              label="去球区行数"
              value={value.removal_rows}
              integer
              allowEmpty
              onChange={(removal_rows) => update({ removal_rows })}
            />
            <NumberInput
              label="去球区列数"
              value={value.removal_columns}
              integer
              allowEmpty
              onChange={(removal_columns) => update({ removal_columns })}
            />
          </Stack>
          <SolderRemovalMatrix
            rows={rows}
            columns={columns}
            omittedCells={value.omitted_cells}
            removalRows={value.removal_rows}
            removalColumns={value.removal_columns}
            onChange={(omitted_cells) => update({ omitted_cells })}
          />
        </>
      )}
    </Stack>
  )
}
