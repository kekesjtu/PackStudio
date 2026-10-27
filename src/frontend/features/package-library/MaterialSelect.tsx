import Chip from '@mui/material/Chip'
import MenuItem from '@mui/material/MenuItem'
import TextField from '@mui/material/TextField'

import FieldShell from '../../ui/FieldShell'
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
    <FieldShell
      label={field.label}
      hint="选择组件材料；材料物性可在右侧材料库中调整"
      disabled={!enabled}
    >
      <TextField
        select
        value={value ?? ''}
        disabled={!enabled}
        size="small"
        slotProps={{
          select: {
            SelectDisplayProps: { 'aria-label': field.label },
            renderValue: (selected) => label(String(selected)),
          },
        }}
        onChange={(event) => onChange(event.target.value)}
      >
        {field.options.map((option) => (
          <MenuItem key={String(option)} value={String(option)}>
            {label(String(option))}
          </MenuItem>
        ))}
      </TextField>
    </FieldShell>
  )
}

function MaterialLabel({ id, material }: { id: string; material?: Material }) {
  const name = material?.name ?? (id || 'No Attachment')
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', minWidth: 0 }}>
      <span title={name} style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
      {material && materialQuality(material) && (
        <Chip size="small" color="warning" label="物性待核实" sx={{ flexShrink: 0 }} />
      )}
    </span>
  )
}
