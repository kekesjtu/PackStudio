import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'

import ColumnResizer from '../model-editor/ColumnResizer'
import ModelPreview from '../model-editor/ModelPreview'
import {
  downloadTemplateModel,
  generateTemplateModel,
  loadTemplateDefaults,
  loadTemplateMaterials,
  loadTemplateSchema,
} from './api'
import PackageInspector from './PackageInspector'
import type {
  Material,
  PackageModel,
  TemplateRequest,
  TemplateSchema,
} from './types'
import WorkspaceNavigation from './WorkspaceNavigation'
import { renderStep, stepTitle } from './WorkspaceSteps'

interface PackageWorkspaceProps {
  templateId: string
}

export default function PackageWorkspace({ templateId }: PackageWorkspaceProps) {
  const [schema, setSchema] = useState<TemplateSchema | null>(null)
  const [request, setRequest] = useState<TemplateRequest | null>(null)
  const [library, setLibrary] = useState<Material[]>([])
  const [model, setModel] = useState<PackageModel | null>(null)
  const [activeStep, setActiveStep] = useState('summary')
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const [hiddenBlockIds, setHiddenBlockIds] = useState<Set<string>>(() => new Set())
  const [propertyWidth, setPropertyWidth] = useState(390)
  const [inspectorWidth, setInspectorWidth] = useState(340)
  const [busy, setBusy] = useState(true)
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const propertyContentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (propertyContentRef.current) propertyContentRef.current.scrollTop = 0
  }, [activeStep])

  useEffect(() => {
    let cancelled = false
    Promise.all([
      loadTemplateSchema(templateId),
      loadTemplateDefaults(templateId),
      loadTemplateMaterials(),
    ])
      .then(async ([loadedSchema, defaults, materials]) => {
        if (cancelled) return
        const generated = await generateTemplateModel(defaults)
        if (cancelled) return
        setSchema(loadedSchema)
        setRequest(defaults)
        setLibrary(materials)
        setModel(generated)
        setActiveStep('packstudio_summary')
        setDirty(false)
        setHiddenBlockIds(new Set())
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
  }, [templateId])

  const allFields = useMemo(
    () => schema?.steps.flatMap((step) => step.fields) ?? [],
    [schema],
  )
  if (schema === null || request === null) {
    return (
      <Box className="package-loading">
        {error ? <Alert severity="error">{error}</Alert> : <CircularProgress />}
      </Box>
    )
  }

  const changeRequest = (next: TemplateRequest) => {
    setRequest(next)
    setDirty(true)
  }
  const handleGenerate = async () => {
    setBusy(true)
    setError(null)
    try {
      const generated = await generateTemplateModel(request)
      setModel(generated)
      setDirty(false)
      setHiddenBlockIds(new Set())
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
      await downloadTemplateModel(request)
    } catch (reason: unknown) {
      setError(errorMessage(reason))
    } finally {
      setBusy(false)
    }
  }
  const hideBlock = (blockId: string, hidden: boolean) => {
    setHiddenBlockIds((current) => {
      const next = new Set(current)
      if (hidden) next.add(blockId)
      else next.delete(blockId)
      return next
    })
  }
  const showOnlyBlock = (blockId: string) => {
    if (!model) return
    setHiddenBlockIds(new Set(model.blocks.map((block) => block.id).filter((id) => id !== blockId)))
  }
  const layoutStyle = {
    '--property-width': `${propertyWidth}px`,
    '--inspector-width': `${inspectorWidth}px`,
  } as CSSProperties

  return (
    <Box component="main" className="template-workspace" style={layoutStyle}>
      <WorkspaceNavigation
        schema={schema}
        activeStep={activeStep}
        onSelect={setActiveStep}
      />
      <Paper component="section" className="property-panel">
        <Box className="property-editor">
          <Typography variant="h5" component="h2" className="panel-heading">
            {stepTitle(schema, activeStep)}
          </Typography>
          <Box ref={propertyContentRef} className="property-content">
            {renderStep(schema, activeStep, allFields, request, library, changeRequest)}
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} className="action-bar">
            <Button variant="contained" disabled={busy} onClick={handleGenerate}>
              {busy ? <CircularProgress size={21} color="inherit" /> : '生成模型'}
            </Button>
            <Button variant="outlined" disabled={busy || !model} onClick={handleExport}>
              导出 FloXML
            </Button>
          </Stack>
        </Box>
      </Paper>
      <ColumnResizer value={propertyWidth} onChange={setPropertyWidth} ariaLabel="调整属性栏宽度" placement="property" />
      <Box className="preview-column">
        {error && <Alert severity="error">{error}</Alert>}
        {model?.warnings?.map((warning) => <Alert severity="warning" key={warning}>{warning}</Alert>)}
        <Paper component="section" className="preview-panel">
          <Stack direction="row" justifyContent="space-between" spacing={1} className="panel-heading preview-heading">
            <Typography variant="h5">三维建模区</Typography>
            <Stack direction="row" spacing={0.75}>
              {model && <Chip size="small" label={`${model.blocks.length} 个块`} />}
              {dirty && <Chip size="small" color="warning" label="参数已修改" />}
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
      <ColumnResizer value={inspectorWidth} onChange={setInspectorWidth} ariaLabel="调整检查器宽度" placement="inspector" deltaDirection={-1} minimum={300} maximum={560} />
      <Paper component="aside" className="inspector-panel">
        <PackageInspector
          model={model}
          library={library}
          request={request}
          selectedBlockId={selectedBlockId}
          hiddenBlockIds={hiddenBlockIds}
          onRequestChange={changeRequest}
          onSelectBlock={setSelectedBlockId}
          onSetBlockHidden={hideBlock}
          onShowOnlyBlock={showOnlyBlock}
          onShowAllBlocks={() => setHiddenBlockIds(new Set())}
        />
      </Paper>
    </Box>
  )
}

const errorMessage = (reason: unknown) => reason instanceof Error ? reason.message : '发生未知错误'
