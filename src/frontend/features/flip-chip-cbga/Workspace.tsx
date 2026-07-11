import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Chip,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material'

import { downloadPtaXml, generateModel } from './api'
import { createDefaultParameters } from './defaults'
import ModelPreview from './ModelPreview'
import ModelTree from './ModelTree'
import ParameterPanel from './ParameterPanel'
import type { FlipChipCbgaParameters, PackageModel } from './types'

const workflowSteps = ['选择模板', '封装参数', '材料与阵列', '热源与边界', '检查并导出']

export default function Workspace() {
  const [parameters, setParameters] = useState(createDefaultParameters)
  const [model, setModel] = useState<PackageModel | null>(null)
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const [busy, setBusy] = useState(true)
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    generateModel(createDefaultParameters())
      .then((generated) => {
        if (cancelled) return
        setModel(generated)
        setSelectedBlockId(generated.blocks[0]?.id ?? null)
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
  }, [])

  const changeParameters = (next: FlipChipCbgaParameters) => {
    setParameters(next)
    setDirty(true)
  }

  const handleGenerate = async () => {
    setBusy(true)
    setError(null)
    try {
      const generated = await generateModel(parameters)
      setModel(generated)
      setDirty(false)
      setSelectedBlockId((current) =>
        generated.blocks.some((block) => block.id === current)
          ? current
          : (generated.blocks[0]?.id ?? null),
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

  return (
    <Box component="main" className="workspace">
      <Paper component="nav" className="workflow-panel" aria-label="建模步骤">
        <Typography variant="overline" color="text.secondary">
          当前模板
        </Typography>
        <Typography variant="h6">Flip Chip CBGA / BGA</Typography>
        <Typography variant="body2" color="text.secondary">
          引导式矩形块热模型
        </Typography>
        <Divider />
        <List disablePadding>
          {workflowSteps.map((step, index) => (
            <ListItemButton key={step} selected={index === 1 || index === 2}>
              <ListItemText primary={`${index + 1}. ${step}`} />
            </ListItemButton>
          ))}
        </List>
        <Alert severity="info" icon={false} className="export-note">
          PTA 文件不包含网格和求解结果；这些数据由 PTA 求解阶段生成。
        </Alert>
      </Paper>

      <Paper component="section" className="parameter-panel">
        <ParameterPanel
          parameters={parameters}
          onChange={changeParameters}
          onGenerate={handleGenerate}
          onExport={handleExport}
          busy={busy}
          exportDisabled={model === null}
        />
      </Paper>

      <Box className="inspection-column">
        {error !== null && <Alert severity="error">{error}</Alert>}
        <Paper component="section" className="preview-panel">
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            spacing={1}
          >
            <Box>
              <Typography variant="h5" component="h2">
                三维预览
              </Typography>
              <Typography color="text.secondary">
                笛卡尔矩形块；拖动旋转，滚轮缩放，点击块定位模型树。
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {model !== null && <Chip label={`${model.blocks.length} 个块`} size="small" />}
              {model !== null && (
                <Chip
                  label={`${String(model.metadata.solder_ball_count)} 个物理焊球`}
                  size="small"
                />
              )}
              {dirty && <Chip label="参数已修改" size="small" color="warning" />}
            </Stack>
          </Stack>
          <ModelPreview
            model={model}
            selectedBlockId={selectedBlockId}
            onSelectBlock={setSelectedBlockId}
          />
        </Paper>
        <Paper component="section" className="tree-panel">
          <Typography variant="h6" component="h2">
            模型树
          </Typography>
          <Typography variant="body2" color="text.secondary">
            分组结构与 PTA 几何对象保持一致。
          </Typography>
          <ModelTree
            model={model}
            selectedBlockId={selectedBlockId}
            onSelectBlock={setSelectedBlockId}
          />
        </Paper>
      </Box>
    </Box>
  )
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : '发生未知错误'
}
