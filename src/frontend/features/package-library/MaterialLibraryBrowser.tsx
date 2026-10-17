import Box from '@mui/material/Box'
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
import type { Material } from './types'

interface MaterialLibraryBrowserProps {
  materials: Material[]
  onChange: (material: Material) => void
}

export default function MaterialLibraryBrowser({
  materials,
  onChange,
}: MaterialLibraryBrowserProps) {
  const [selectedId, setSelectedId] = useState('')
  const selected = materials.find((material) => material.id === selectedId) ?? materials[0]
  if (!selected) {
    return <Typography color="text.secondary">材料库为空。</Typography>
  }
  const isotropic =
    selected.conductivity.x === selected.conductivity.y &&
    selected.conductivity.y === selected.conductivity.z

  return (
    <Box className="material-browser">
      <List dense disablePadding className="material-browser-list">
        {materials.map((material) => (
          <ListItemButton
            key={material.id}
            selected={material.id === selected.id}
            onClick={() => setSelectedId(material.id)}
          >
            <Box className="material-swatch" sx={{ backgroundColor: material.color }} />
            <ListItemText primary={material.name} secondary={material.id} sx={{ ml: 1 }} />
            {materialQuality(material) && <Chip size="small" color="warning" label="物性待核实" />}
          </ListItemButton>
        ))}
      </List>
      <Box className="material-browser-details">
        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
          <Typography variant="subtitle2">{selected.name}</Typography>
          <Chip
            size="small"
            variant="outlined"
            label={isotropic ? '各向同性' : '正交各向异性'}
          />
        </Stack>
        <Typography variant="caption" color="text.secondary">
          修改会保存为当前方案的材料覆盖值，不会改写 PackStudio 内置材料库。
        </Typography>
        <Property label="材料 ID" value={selected.id} />
        <TextField
          label="名称"
          size="small"
          value={selected.name}
          onChange={(event) => onChange({ ...selected, name: event.target.value })}
        />
        <TextField
          label="颜色"
          type="color"
          size="small"
          value={selected.color}
          slotProps={{ inputLabel: { shrink: true } }}
          onChange={(event) => onChange({ ...selected, color: event.target.value })}
        />
        <MaterialFields material={selected} showTitle={false} onChange={onChange} />
        {selected.source && <Property label="来源" value={selected.source} />}
      </Box>
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
