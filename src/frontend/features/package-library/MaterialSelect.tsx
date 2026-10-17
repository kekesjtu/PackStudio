import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import MenuItem from '@mui/material/MenuItem'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import materialQuality from '../model-editor/materialQuality'
import type { Material, WizardField, WizardValue } from './types'

interface MaterialSelectProps {
  field: WizardField
  value: WizardValue
  enabled: boolean
  materials: Material[]
  onChange: (value: WizardValue) => void
}

export default function MaterialSelect({ field, value, enabled, materials, onChange }: MaterialSelectProps) {
  const label = (id: string) => <MaterialLabel id={id} material={materials.find((item) => item.id === id)} />
  return (
    <TextField
      select
      label={field.label}
      value={value ?? ''}
      disabled={!enabled}
      size="small"
      helperText="选择组件材料；材料物性可在右侧材料库中调整"
      slotProps={{ select: { renderValue: (selected) => label(String(selected)) } }}
      onChange={(event) => onChange(event.target.value)}
    >
      {field.options.map((option) => (
        <MenuItem key={String(option)} value={String(option)}>
          {label(String(option))}
        </MenuItem>
      ))}
    </TextField>
  )
}

function MaterialLabel({ id, material }: { id: string; material?: Material }) {
  const name = material?.name ?? id
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%', minWidth: 0 }}>
      <Typography component="span" title={name} sx={{ flex: 1, minWidth: 0 }} noWrap>{name}</Typography>
      {material && materialQuality(material) && (
        <Chip size="small" color="warning" label="物性待核实" sx={{ flexShrink: 0 }} />
      )}
    </Box>
  )
}
