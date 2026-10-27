import Box from '@mui/material/Box'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import { useMemo, useState } from 'react'

import ModelTree from '../model-editor/ModelTree'
import MaterialLibraryBrowser from './MaterialLibraryBrowser'
import type { Material, PackageModel, TemplateRequest } from './types'

interface PackageInspectorProps {
  model: PackageModel | null
  library: Material[]
  request: TemplateRequest
  selectedBlockIds: ReadonlySet<string>
  hiddenBlockIds: ReadonlySet<string>
  onRequestChange: (request: TemplateRequest) => void
  onSelectBlocks: (blockIds: string[]) => void
  onSetBlockHidden: (blockId: string, hidden: boolean) => void
  onShowOnlyBlock: (blockId: string) => void
  onShowAllBlocks: () => void
}

export default function PackageInspector(props: PackageInspectorProps) {
  const [tab, setTab] = useState<'materials' | 'tree'>('materials')
  const materials = useMemo(
    () => mergeMaterials(props.library, props.request.custom_materials),
    [props.library, props.request.custom_materials],
  )
  return (
    <Box className="inspector-content">
      <Tabs
        value={tab}
        onChange={(_event, value: 'materials' | 'tree') => setTab(value)}
        variant="fullWidth"
      >
        <Tab value="materials" label="材料库" />
        <Tab value="tree" label="模型树" />
      </Tabs>
      <Box className="inspector-tab-content">
        {tab === 'tree' ? (
          <ModelTree
            model={props.model}
            selectedBlockIds={props.selectedBlockIds}
            hiddenBlockIds={props.hiddenBlockIds}
            onSelectBlocks={props.onSelectBlocks}
            onSetBlockHidden={props.onSetBlockHidden}
            onShowOnlyBlock={props.onShowOnlyBlock}
            onShowAllBlocks={props.onShowAllBlocks}
          />
        ) : (
          <MaterialLibraryBrowser
            materials={materials}
            onChange={(material) =>
              props.onRequestChange({
                ...props.request,
                custom_materials: [
                  ...props.request.custom_materials.filter(
                    (item) => item.id !== material.id,
                  ),
                  material,
                ],
              })
            }
          />
        )}
      </Box>
    </Box>
  )
}

function mergeMaterials(...collections: Material[][]) {
  const merged = new Map<string, Material>()
  for (const collection of collections) {
    for (const material of collection) merged.set(material.id, material)
  }
  return [...merged.values()]
}
