import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Chip from '@mui/material/Chip'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import MaterialFields from '../model-editor/MaterialFields'
import materialQuality from '../model-editor/materialQuality'
import FieldShell from '../../ui/FieldShell'
import type { Material } from './types'
import { groupedMaterials } from './materialGroups'

interface MaterialLibraryBrowserProps {
  materials: Material[]
  onChange: (material: Material) => void
}

export default function MaterialLibraryBrowser({
  materials,
  onChange,
}: MaterialLibraryBrowserProps) {
  const [selectedId, setSelectedId] = useState('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(() => new Set())
  const selected = materials.find((material) => material.id === selectedId)
  const available = new Map(materials.map((material) => [material.id, material]))
  const groups = groupedMaterials({ options: materials.map((material) => material.id) }, materials)
  if (materials.length === 0) {
    return <Typography color="text.secondary">材料库为空。</Typography>
  }
  const isotropic =
    selected && selected.conductivity.x === selected.conductivity.y &&
    selected.conductivity.y === selected.conductivity.z

  return (
    <Box className="material-browser" data-has-selection={Boolean(selected)}>
      <List dense disablePadding className="material-browser-list" aria-label="材料分组">
        {[...groups].map(([category, ids]) => {
          const expanded = expandedCategories.has(category)
          return (
            <Box component="li" key={category} className="material-browser-group">
              <ButtonBase className="material-group-toggle" aria-expanded={expanded}
                aria-label={`${expanded ? '折叠' : '展开'} ${category}`}
                onClick={() => setExpandedCategories((current) => {
                  const next = new Set(current)
                  if (next.has(category)) next.delete(category)
                  else next.add(category)
                  return next
                })}>
                <span className="material-group-chevron" aria-hidden="true">{expanded ? '−' : '+'}</span>
                <span>{category}</span> <span className="material-group-count">({ids.length})</span>
              </ButtonBase>
              {expanded && <List dense disablePadding aria-label={category}>
                {ids.map((id) => {
                  const material = available.get(id)!
                  return (
                    <ListItemButton
                      key={material.id}
                      selected={material.id === selected?.id}
                      onClick={() => setSelectedId(material.id)}
                    >
                      <Box className="material-swatch" sx={{ backgroundColor: material.color }} />
                      <ListItemText primary={material.name} secondary={material.id} sx={{ ml: 1 }} />
                      {materialQuality(material) && <Chip size="small" color="warning" label="物性待核实" />}
                    </ListItemButton>
                  )
                })}
              </List>}
            </Box>
          )
        })}
      </List>
      {selected && <Box className="material-browser-details" role="region" aria-label="材料属性">
        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
          <Typography variant="subtitle2">{selected.name}</Typography>
          <Chip
            size="small"
            variant="outlined"
            label={isotropic ? '各向同性' : '正交各向异性'}
          />
        </Stack>
        <Property label="材料 ID" value={selected.id} />
        <FieldShell label="名称">
          <TextField
            size="small"
            value={selected.name}
            slotProps={{ htmlInput: { 'aria-label': '名称' } }}
            onChange={(event) => onChange({ ...selected, name: event.target.value })}
          />
        </FieldShell>
        <FieldShell label="颜色">
          <Box className="color-field-row">
            <TextField
              type="color"
              size="small"
              className="color-field-input"
              value={selected.color}
              slotProps={{ htmlInput: { 'aria-label': '颜色' } }}
              onChange={(event) => onChange({ ...selected, color: event.target.value })}
            />
            <Typography component="span" className="color-field-value">
              {selected.color.toUpperCase()}
            </Typography>
          </Box>
        </FieldShell>
        <MaterialFields material={selected} showTitle={false} onChange={onChange} />
        {selected.source && <Property label="来源" value={selected.source} />}
      </Box>}
    </Box>
  )
}

function Property({ label, value }: { label: string; value: string }) {
  return (
    <Box className="material-browser-property">
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  )
}
