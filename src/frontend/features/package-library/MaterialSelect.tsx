import Chip from '@mui/material/Chip'
import MenuItem from '@mui/material/MenuItem'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import { useState } from 'react'

import FieldShell from '../../ui/FieldShell'
import materialQuality from '../model-editor/materialQuality'
import { groupedMaterials } from './materialGroups'
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
  const groups = groupedMaterials(field, materials)
  const categoryOf = (id: string) => [...groups].find(([, ids]) => ids.includes(id))?.[0]
  const [emptyCategory, setEmptyCategory] = useState(categoryOf(String(field.default)) ?? '')
  const category = categoryOf(String(value)) ?? (groups.has(emptyCategory) ? emptyCategory : groups.keys().next().value ?? '')
  const members = groups.get(category) ?? []
  return (
    <Stack spacing={1}>
      <FieldShell label={`${field.label}组`} disabled={!enabled}>
        <TextField select size="small" value={category} disabled={!enabled}
          slotProps={{ select: { SelectDisplayProps: { 'aria-label': `${field.label}组` } } }}
          onChange={(event) => {
            const selected = event.target.value
            const candidates = groups.get(selected) ?? []
            setEmptyCategory(selected)
            const defaultId = String(field.default)
            onChange(candidates.includes(defaultId) ? defaultId : candidates[0])
          }}>
          {[...groups.keys()].map((group) => <MenuItem key={group} value={group}>{group}</MenuItem>)}
        </TextField>
      </FieldShell>
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
              displayEmpty: true,
              SelectDisplayProps: { 'aria-label': field.label },
              renderValue: (selected) => label(String(selected)),
            },
          }}
          onChange={(event) => {
            setEmptyCategory(category)
            onChange(event.target.value)
          }}
        >
          {field.options.includes('') && <MenuItem value="">No Attachment</MenuItem>}
          {members.map((option) => (
            <MenuItem key={String(option)} value={String(option)}>
              {label(String(option))}
            </MenuItem>
          ))}
        </TextField>
      </FieldShell>
    </Stack>
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
