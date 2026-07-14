import { useRef, useState, type CSSProperties } from 'react'
import {
  Box,
  Chip,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import { materialUsageLabels } from './materialBindings'
import MaterialFields from './MaterialFields'
import RowResizer from './RowResizer'
import type { FlipChipCbgaParameters, Material } from './types'

interface MaterialLibraryPanelProps {
  materials: Material[]
  parameters: FlipChipCbgaParameters
  selectedMaterialId: string
  onSelect: (materialId: string) => void
  onChange: (material: Material) => void
}

export default function MaterialLibraryPanel({
  materials,
  parameters,
  selectedMaterialId,
  onSelect,
  onChange,
}: MaterialLibraryPanelProps) {
  const [listHeight, setListHeight] = useState(240)
  const panelRef = useRef<HTMLDivElement>(null)
  const selected = materials.find((material) => material.id === selectedMaterialId) ?? materials[0]
  if (selected === undefined) return null
  const usages = materialUsageLabels(parameters, selected.id)
  const layoutStyle = { '--material-list-height': `${listHeight}px` } as CSSProperties

  return (
    <Box ref={panelRef} className="material-library-panel" style={layoutStyle}>
      <Box className="material-library-list">
        <List dense disablePadding>
          {materials.map((material) => (
            <ListItemButton
              key={material.id}
              selected={material.id === selected.id}
              onClick={() => onSelect(material.id)}
            >
              <Box className="material-swatch" sx={{ backgroundColor: material.color }} />
              <ListItemText primary={material.name} secondary={material.id} sx={{ ml: 1 }} />
            </ListItemButton>
          ))}
        </List>
      </Box>
      <RowResizer
        value={listHeight}
        onChange={setListHeight}
        containerRef={panelRef}
        ariaLabel="调整材料列表和属性区域高度"
      />
      <Box className="material-property-editor">
        <Typography variant="subtitle2">材料属性</Typography>
        <TextField
          label="名称"
          size="small"
          value={selected.name}
          onChange={(event) => onChange({ ...selected, name: event.target.value })}
          fullWidth
        />
        <Stack direction="row" spacing={1} alignItems="center">
          <TextField
            label="颜色"
            type="color"
            size="small"
            value={selected.color}
            onChange={(event) => onChange({ ...selected, color: event.target.value })}
            slotProps={{ inputLabel: { shrink: true } }}
            sx={{ width: 96 }}
          />
          <Typography variant="caption" color="text.secondary">
            {selected.id}
          </Typography>
        </Stack>
        <MaterialFields material={selected} onChange={onChange} showTitle={false} />
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {usages.map((usage) => (
            <Chip key={usage} label={usage} size="small" variant="outlined" />
          ))}
        </Stack>
      </Box>
    </Box>
  )
}
