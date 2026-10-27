import Alert from '@mui/material/Alert'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import NumberInput from '../model-editor/NumberInput'
import SolderRemovalMatrix from './SolderRemovalMatrix'
import type { BgaConfiguration } from './types'

export default function NativeBgaPanel({ value, rows, columns, section, onChange }: {
  value: BgaConfiguration; rows: number; columns: number; section: 'center' | 'removal'
  onChange: (value: BgaConfiguration) => void
}) {
  const update = (patch: Partial<BgaConfiguration>) => onChange({ ...value, ...patch })
  const center = section === 'center'
  const enabled = center ? value.center_solder_enabled
    : value.depopulated_center ?? value.solder_removal_enabled
  return <Stack spacing={1.5}>
    <FormControlLabel label={center ? '中央焊球' : '中央去球'} control={<Switch checked={enabled}
      onChange={(e) => update(center ? { center_solder_enabled: e.target.checked }
        : { depopulated_center: e.target.checked, solder_removal_enabled: e.target.checked || value.omitted_cells.length > 0 })} />} />
    {enabled && <>
      <Stack direction="row" spacing={1}>
        <NumberInput label={center ? '中央行数 MEc' : '外围满布行数 MEp'} integer allowEmpty
          value={center ? value.center_solder_rows : value.populated_rows ?? (value.removal_rows === null ? null : rows - value.removal_rows)}
          onChange={(n) => update(center ? { center_solder_rows: n } : { populated_rows: n })} />
        <NumberInput label={center ? '中央列数 MDc' : '外围满布列数 MDp'} integer allowEmpty
          value={center ? value.center_solder_columns : value.populated_columns ?? (value.removal_columns === null ? null : columns - value.removal_columns)}
          onChange={(n) => update(center ? { center_solder_columns: n } : { populated_columns: n })} />
      </Stack>
      {center && <FormControlLabel label="中央阵列 Staggered" control={<Switch checked={value.center_staggered ?? false}
        onChange={(e) => update({ center_staggered: e.target.checked })} />} />}
    </>}
    {!center && <>
      <Alert severity="info">显式去球名单覆盖中央去球和主阵列 Staggered。MEp、MDp 是两侧合计的外围满布行列数。</Alert>
      <SolderRemovalMatrix rows={rows} columns={columns} omittedCells={value.omitted_cells}
        removalRows={0} removalColumns={0} onChange={(omitted_cells) => update({ omitted_cells,
          solder_removal_enabled: enabled || omitted_cells.length > 0,
          representation: omitted_cells.length ? 'discrete' : value.representation })} />
    </>}
  </Stack>
}
