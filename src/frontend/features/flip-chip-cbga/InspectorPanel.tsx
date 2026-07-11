import { Box, Tab, Tabs } from '@mui/material'
import { useState } from 'react'

import MaterialLibraryPanel from './MaterialLibraryPanel'
import ModelTree from './ModelTree'
import type { FlipChipCbgaParameters, Material, PackageModel } from './types'

interface InspectorPanelProps {
  model: PackageModel | null
  parameters: FlipChipCbgaParameters
  materials: Material[]
  selectedMaterialId: string
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectMaterial: (materialId: string) => void
  onChangeMaterial: (material: Material) => void
  onSelectBlock: (blockId: string) => void
  onSetBlockHidden: (blockId: string, hidden: boolean) => void
  onShowOnlyBlock: (blockId: string) => void
  onShowAllBlocks: () => void
}

export default function InspectorPanel(props: InspectorPanelProps) {
  const [tab, setTab] = useState<'materials' | 'tree'>('materials')
  return (
    <Box className="inspector-content">
      <Tabs value={tab} onChange={(_event, value: 'materials' | 'tree') => setTab(value)} variant="fullWidth">
        <Tab value="materials" label="材料库" />
        <Tab value="tree" label="模型树" />
      </Tabs>
      <Box className="inspector-tab-content">
        {tab === 'materials' ? (
          <MaterialLibraryPanel
            materials={props.materials}
            parameters={props.parameters}
            selectedMaterialId={props.selectedMaterialId}
            onSelect={props.onSelectMaterial}
            onChange={props.onChangeMaterial}
          />
        ) : (
          <ModelTree
            model={props.model}
            selectedBlockId={props.selectedBlockId}
            hiddenBlockIds={props.hiddenBlockIds}
            onSelectBlock={props.onSelectBlock}
            onSetBlockHidden={props.onSetBlockHidden}
            onShowOnlyBlock={props.onShowOnlyBlock}
            onShowAllBlocks={props.onShowAllBlocks}
          />
        )}
      </Box>
    </Box>
  )
}
