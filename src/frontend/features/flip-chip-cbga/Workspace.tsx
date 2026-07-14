import { useEffect, useState, type CSSProperties } from 'react'
import { Alert, Box, Chip, Paper, Stack, Typography } from '@mui/material'

import { downloadPtaXml, generateModel } from './api'
import ColumnResizer from './ColumnResizer'
import { createDefaultParameters } from './defaults'
import InspectorPanel from './InspectorPanel'
import {
  collectMaterialLibrary,
  replaceMaterialDefinition,
} from './materialBindings'
import ModelPreview from './ModelPreview'
import { loadSavedParameters, saveParameters } from './parameterStorage'
import PropertyNavigation from './PropertyNavigation'
import PropertyPanel from './PropertyPanel'
import type { PropertySectionId } from './propertySections'
import type { FlipChipCbgaParameters, Material, PackageModel } from './types'

export default function Workspace() {
  const [initialState] = useState(() => {
    const saved = loadSavedParameters()
    return { parameters: saved ?? createDefaultParameters(), restored: saved !== null }
  })
  const [parameters, setParameters] = useState(initialState.parameters)
  const [materials, setMaterials] = useState(() => collectMaterialLibrary(initialState.parameters))
  const [model, setModel] = useState<PackageModel | null>(null)
  const [activeSection, setActiveSection] = useState<PropertySectionId>('summary')
  const [selectedMaterialId, setSelectedMaterialId] = useState('alumina')
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const [hiddenBlockIds, setHiddenBlockIds] = useState<Set<string>>(() => new Set())
  const [propertyWidth, setPropertyWidth] = useState(380)
  const [inspectorWidth, setInspectorWidth] = useState(320)
  const [busy, setBusy] = useState(true)
  const [dirty, setDirty] = useState(false)
  const [parametersSaved, setParametersSaved] = useState(initialState.restored)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    generateModel(initialState.parameters)
      .then((generated) => {
        if (cancelled) return
        setModel(generated)
        setSelectedBlockId(null)
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(errorMessage(reason))
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [initialState.parameters])

  const changeParameters = (next: FlipChipCbgaParameters) => {
    setParameters(next)
    setDirty(true)
    setParametersSaved(false)
  }

  const changeMaterial = (material: Material) => {
    setMaterials((current) =>
      current.map((item) => (item.id === material.id ? material : item)),
    )
    setParameters((current) => replaceMaterialDefinition(current, material))
    setDirty(true)
    setParametersSaved(false)
  }

  const handleSaveParameters = () => {
    setError(null)
    try {
      saveParameters(parameters)
      setParametersSaved(true)
    } catch (reason: unknown) {
      setError(errorMessage(reason))
    }
  }

  const handleGenerate = async () => {
    setBusy(true)
    setError(null)
    try {
      const generated = await generateModel(parameters)
      setModel(generated)
      setDirty(false)
      setHiddenBlockIds(new Set())
      setSelectedBlockId((current) =>
        current !== null && generated.blocks.some((block) => block.id === current)
          ? current
          : null,
      )
    } catch (reason: unknown) {
      setError(errorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  const handleExport = async () => {
    setBusy(true)
    setError(null)
    try {
      await downloadPtaXml(parameters)
    } catch (reason: unknown) {
      setError(errorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  const setBlockHidden = (blockId: string, hidden: boolean) => {
    setHiddenBlockIds((current) => {
      const next = new Set(current)
      if (hidden) next.add(blockId)
      else next.delete(blockId)
      return next
    })
  }

  const showOnlyBlock = (blockId: string) => {
    if (model === null) return
    setHiddenBlockIds(new Set(model.blocks.map((block) => block.id).filter((id) => id !== blockId)))
    setSelectedBlockId(blockId)
  }

  const layoutStyle = {
    '--property-width': `${propertyWidth}px`,
    '--inspector-width': `${inspectorWidth}px`,
  } as CSSProperties

  return (
    <Box component="main" className="template-workspace" style={layoutStyle}>
      <PropertyNavigation activeSection={activeSection} onChange={setActiveSection} />
      <Paper component="section" className="property-panel">
        <PropertyPanel
          activeSection={activeSection}
          parameters={parameters}
          materials={materials}
          model={model}
          onChange={changeParameters}
          onGenerate={handleGenerate}
          onSaveParameters={handleSaveParameters}
          onExport={handleExport}
          busy={busy}
        />
      </Paper>
      <ColumnResizer
        value={propertyWidth}
        onChange={setPropertyWidth}
        ariaLabel="调整属性栏宽度"
        placement="property"
      />
      <Box className="preview-column">
        {error !== null && <Alert severity="error">{error}</Alert>}
        <Paper component="section" className="preview-panel">
          <Stack direction="row" justifyContent="space-between" spacing={1}>
            <Typography variant="h5" component="h2">
              三维建模区
            </Typography>
            <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
              {model !== null && <Chip label={`${model.blocks.length} 个块`} size="small" />}
              {hiddenBlockIds.size > 0 && (
                <Chip label={`隐藏 ${hiddenBlockIds.size}`} size="small" color="warning" />
              )}
              {dirty && <Chip label="参数已修改" size="small" color="warning" />}
              {parametersSaved && <Chip label="参数已保存" size="small" color="success" />}
            </Stack>
          </Stack>
          <ModelPreview
            model={model}
            selectedBlockId={selectedBlockId}
            hiddenBlockIds={hiddenBlockIds}
            onSelectBlock={setSelectedBlockId}
          />
        </Paper>
      </Box>
      <ColumnResizer
        value={inspectorWidth}
        onChange={setInspectorWidth}
        ariaLabel="调整检查器宽度"
        placement="inspector"
        deltaDirection={-1}
        minimum={280}
        maximum={520}
      />
      <Paper component="aside" className="inspector-panel">
        <InspectorPanel
          model={model}
          parameters={parameters}
          materials={materials}
          selectedMaterialId={selectedMaterialId}
          selectedBlockId={selectedBlockId}
          hiddenBlockIds={hiddenBlockIds}
          onSelectMaterial={setSelectedMaterialId}
          onChangeMaterial={changeMaterial}
          onSelectBlock={setSelectedBlockId}
          onSetBlockHidden={setBlockHidden}
          onShowOnlyBlock={showOnlyBlock}
          onShowAllBlocks={() => setHiddenBlockIds(new Set())}
        />
      </Paper>
    </Box>
  )
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : '发生未知错误'
}
