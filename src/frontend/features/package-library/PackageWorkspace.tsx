import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'

import ColumnResizer from '../model-editor/ColumnResizer'
import ModelPreview from '../model-editor/ModelPreview'
import NumberInput from '../model-editor/NumberInput'
import {
  downloadTemplatePta,
  generateTemplateModel,
  loadTemplateDefaults,
  loadTemplateMaterials,
  loadTemplateSchema,
} from './api'
import BgaConfigurationPanel from './BgaConfigurationPanel'
import PackageInspector from './PackageInspector'
import { restoreTemplateRequest, saveTemplateRequest } from './requestStorage'
import type {
  Material,
  PackageModel,
  TemplateRequest,
  TemplateSchema,
} from './types'
import WizardFields from './WizardFields'

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
  const [saved, setSaved] = useState(false)
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
        const restored = restoreTemplateRequest(templateId, defaults, loadedSchema)
        const initialRequest = restored ?? defaults
        const generated = await generateTemplateModel(initialRequest)
        if (cancelled) return
        setSchema(loadedSchema)
        setRequest(initialRequest)
        setLibrary(materials)
        setModel(generated)
        setActiveStep(loadedSchema.steps[0]?.id ?? 'common')
        setSaved(restored !== null)
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
    setSaved(false)
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
      await downloadTemplatePta(request)
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
      <Paper component="nav" className="structure-navigation">
        <Typography variant="subtitle2">引导步骤</Typography>
        <List dense disablePadding>
          {schema.steps.map((step) => (
            <ListItemButton
              key={step.id}
              selected={activeStep === step.id}
              onClick={() => setActiveStep(step.id)}
            >
              <ListItemText primary={step.label} />
            </ListItemButton>
          ))}
          {schema.has_bga && (
            <ListItemButton selected={activeStep === 'packstudio_bga'} onClick={() => setActiveStep('packstudio_bga')}>
              <ListItemText primary="BGA 焊球配置" />
            </ListItemButton>
          )}
          <ListItemButton selected={activeStep === 'packstudio_common'} onClick={() => setActiveStep('packstudio_common')}>
            <ListItemText primary="热源与网格" />
          </ListItemButton>
          <ListItemButton selected={activeStep === 'packstudio_boundary'} onClick={() => setActiveStep('packstudio_boundary')}>
            <ListItemText primary="边界条件" />
          </ListItemButton>
        </List>
      </Paper>
      <Paper component="section" className="property-panel">
        <Box className="property-editor">
          <Typography variant="h5" component="h2">
            {stepTitle(schema, activeStep)}
          </Typography>
          <Divider />
          <Box ref={propertyContentRef} className="property-content">
            {renderStep(schema, activeStep, allFields, request, library, changeRequest)}
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} className="action-bar">
            <Button variant="contained" disabled={busy} onClick={handleGenerate}>
              {busy ? <CircularProgress size={21} color="inherit" /> : '生成模型'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => {
                saveTemplateRequest(templateId, request)
                setSaved(true)
              }}
            >
              保存参数
            </Button>
            <Button variant="outlined" disabled={busy || !model} onClick={handleExport}>
              导出 PTA XML
            </Button>
          </Stack>
        </Box>
      </Paper>
      <ColumnResizer value={propertyWidth} onChange={setPropertyWidth} ariaLabel="调整属性栏宽度" placement="property" />
      <Box className="preview-column">
        {error && <Alert severity="error">{error}</Alert>}
        <Paper component="section" className="preview-panel">
          <Stack direction="row" justifyContent="space-between" spacing={1}>
            <Typography variant="h5">三维建模区</Typography>
            <Stack direction="row" spacing={0.75}>
              {model && <Chip size="small" label={`${model.blocks.length} 个块`} />}
              {dirty && <Chip size="small" color="warning" label="参数已修改" />}
              {saved && <Chip size="small" color="success" label="参数已保存" />}
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

function renderStep(
  schema: TemplateSchema,
  activeStep: string,
  allFields: TemplateSchema['steps'][number]['fields'],
  request: TemplateRequest,
  materials: Material[],
  onChange: (request: TemplateRequest) => void,
) {
  if (activeStep === 'packstudio_bga' && request.bga) {
    return <BgaConfigurationPanel value={request.bga} onChange={(bga) => onChange({ ...request, bga })} />
  }
  if (activeStep === 'packstudio_common') return <CommonFields request={request} onChange={onChange} />
  if (activeStep === 'packstudio_boundary') return <BoundaryFields request={request} onChange={onChange} />
  const step = schema.steps.find((item) => item.id === activeStep) ?? schema.steps[0]
  return <WizardFields step={step} allFields={allFields} request={request} materials={materials} onChange={onChange} />
}

function CommonFields({ request, onChange }: { request: TemplateRequest; onChange: (value: TemplateRequest) => void }) {
  return (
    <Stack spacing={2}>
      <TextField size="small" label="设计名称" value={request.design_name ?? ''} onChange={(event) => onChange({ ...request, design_name: event.target.value })} />
      <NumberInput label="芯片总功率" unit="W" value={request.die_power_w} onChange={(die_power_w) => onChange({ ...request, die_power_w })} />
      <TextField select size="small" label="最大网格尺寸预设" value={request.mesh.resolution} onChange={(event) => onChange({ ...request, mesh: { resolution: event.target.value as TemplateRequest['mesh']['resolution'] } })}>
        <MenuItem value="coarse">粗</MenuItem><MenuItem value="standard">标准</MenuItem><MenuItem value="fine">细</MenuItem>
      </TextField>
    </Stack>
  )
}

function BoundaryFields({ request, onChange }: { request: TemplateRequest; onChange: (value: TemplateRequest) => void }) {
  const update = (patch: Partial<TemplateRequest['environment']>) => onChange({ ...request, environment: { ...request.environment, ...patch } })
  return <Stack spacing={2}>
    <NumberInput label="环境温度" unit="K" value={request.environment.ambient_temperature_k} onChange={(value) => update({ ambient_temperature_k: value ?? 0 })} />
    <NumberInput label="普通外表面对流" unit="W/(m²·K)" value={request.environment.default_convection_coefficient_w_m2k} onChange={(value) => update({ default_convection_coefficient_w_m2k: value ?? 0 })} />
    <NumberInput label="PCB 侧换热系数" unit="W/(m²·K)" value={request.environment.pcb_convection_coefficient_w_m2k} onChange={(value) => update({ pcb_convection_coefficient_w_m2k: value ?? 0 })} />
    <NumberInput label="顶部换热系数" unit="W/(m²·K)" value={request.environment.top_convection_coefficient_w_m2k} onChange={(value) => update({ top_convection_coefficient_w_m2k: value ?? 0 })} />
  </Stack>
}

function stepTitle(schema: TemplateSchema, stepId: string) {
  if (stepId === 'packstudio_bga') return 'BGA 焊球配置'
  if (stepId === 'packstudio_common') return '热源与网格'
  if (stepId === 'packstudio_boundary') return '边界条件'
  return schema.steps.find((step) => step.id === stepId)?.label ?? '参数'
}

const errorMessage = (reason: unknown) => reason instanceof Error ? reason.message : '发生未知错误'
