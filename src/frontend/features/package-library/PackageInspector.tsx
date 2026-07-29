import { Box, MenuItem, Stack, Tab, Tabs, TextField, Typography } from '@mui/material'
import { useMemo, useState } from 'react'

import MaterialFields from '../flip-chip-cbga/MaterialFields'
import ModelTree from '../flip-chip-cbga/ModelTree'
import type {
  Material,
  PackageModel,
  TemplateRequest,
} from './types'

interface PackageInspectorProps {
  model: PackageModel | null
  library: Material[]
  request: TemplateRequest
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onRequestChange: (request: TemplateRequest) => void
  onSelectBlock: (blockId: string) => void
  onSetBlockHidden: (blockId: string, hidden: boolean) => void
  onShowOnlyBlock: (blockId: string) => void
  onShowAllBlocks: () => void
}

export default function PackageInspector(props: PackageInspectorProps) {
  const [tab, setTab] = useState<'materials' | 'tree'>('materials')
  const materials = useMemo(
    () => mergeMaterials(props.library, props.model?.materials ?? [], props.request.custom_materials),
    [props.library, props.model, props.request.custom_materials],
  )
  const [selectedMaterialId, setSelectedMaterialId] = useState('')
  const selected =
    materials.find((material) => material.id === selectedMaterialId) ?? materials[0]
  return (
    <Box className="inspector-content">
      <Tabs
        value={tab}
        onChange={(_event, value: 'materials' | 'tree') => setTab(value)}
        variant="fullWidth"
      >
        <Tab value="materials" label="材料配置" />
        <Tab value="tree" label="模型树" />
      </Tabs>
      <Box className="inspector-tab-content">
        {tab === 'tree' ? (
          <ModelTree
            model={props.model}
            selectedBlockId={props.selectedBlockId}
            hiddenBlockIds={props.hiddenBlockIds}
            onSelectBlock={props.onSelectBlock}
            onSetBlockHidden={props.onSetBlockHidden}
            onShowOnlyBlock={props.onShowOnlyBlock}
            onShowAllBlocks={props.onShowAllBlocks}
          />
        ) : (
          <Stack spacing={2} className="package-materials">
            <Typography variant="subtitle2">按结构组绑定材料</Typography>
            {props.model?.groups
              .filter((group) => group.id !== 'package')
              .map((group) => (
                <TextField
                  key={group.id}
                  select
                  size="small"
                  label={group.name}
                  value={assignmentForGroup(group.id, props.request)}
                  onChange={(event) => {
                    const assignments = { ...props.request.material_assignments }
                    if (event.target.value) assignments[group.id] = event.target.value
                    else delete assignments[group.id]
                    props.onRequestChange({
                      ...props.request,
                      material_assignments: assignments,
                    })
                  }}
                >
                  <MenuItem value="">保持参考材料</MenuItem>
                  {materials.map((material) => (
                    <MenuItem key={material.id} value={material.id}>
                      {material.name}
                    </MenuItem>
                  ))}
                </TextField>
              ))}
            {selected && (
              <>
                <TextField
                  select
                  size="small"
                  label="编辑材料属性"
                  value={selected.id}
                  onChange={(event) => setSelectedMaterialId(event.target.value)}
                >
                  {materials.map((material) => (
                    <MenuItem key={material.id} value={material.id}>
                      {material.name}
                    </MenuItem>
                  ))}
                </TextField>
                <MaterialFields
                  material={selected}
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
              </>
            )}
          </Stack>
        )}
      </Box>
    </Box>
  )
}

function assignmentForGroup(
  groupId: string,
  request: TemplateRequest,
) {
  return request.material_assignments[groupId] ?? ''
}

function mergeMaterials(...collections: Material[][]) {
  const merged = new Map<string, Material>()
  for (const collection of collections) {
    for (const material of collection) merged.set(material.id, material)
  }
  return [...merged.values()]
}
