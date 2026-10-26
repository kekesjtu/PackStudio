import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../../src/frontend/features/package-library/api'
import PackageWorkspace from '../../src/frontend/features/package-library/PackageWorkspace'
import { model, request, safe, schema, suspect } from './materialQualityFixtures'

vi.mock('../../src/frontend/features/package-library/api')
vi.mock('../../src/frontend/features/model-editor/ModelPreview', () => ({ default: () => null }))

beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(api.loadTemplateSchema).mockResolvedValue(schema)
  vi.mocked(api.loadTemplateDefaults).mockResolvedValue(request)
  vi.mocked(api.loadTemplateMaterials).mockResolvedValue([safe, suspect])
  vi.mocked(api.generateTemplateModel).mockResolvedValue(model)
  vi.mocked(api.downloadTemplateModel).mockResolvedValue()
})

describe('workspace compact material labels and exports', () => {
  it('shows labels without a central warning for the initial design', async () => {
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    expect(screen.getByText('物性待核实')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(api.generateTemplateModel).toHaveBeenCalledWith(request)
    expect(api.downloadTemplateModel).not.toHaveBeenCalled()
  })

  it('exports the current request to FloXML without a central warning', async () => {
    vi.mocked(api.loadTemplateSchema).mockResolvedValue({ ...schema, steps: [] })
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('设计名称'), { target: { value: '当前修改' } })
    expect(screen.queryByLabelText('导出格式')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /^导出 / }))
    await waitFor(() => expect(api.downloadTemplateModel).toHaveBeenCalledOnce())
    expect(api.generateTemplateModel).toHaveBeenCalledOnce()
    expect(api.downloadTemplateModel).toHaveBeenCalledWith({ ...request, design_name: '当前修改' })
    expect(screen.queryByText('材料热容数据警告')).not.toBeInTheDocument()
  })

  it('removes the material label after both properties are corrected', async () => {
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    fireEvent.click(screen.getByRole('button', { name: /芯片胶.*adhesive/ }))
    fireEvent.change(screen.getByLabelText('密度'), { target: { value: '2200' } })
    fireEvent.change(screen.getByLabelText('比热'), { target: { value: '900' } })
    expect(screen.queryByText('材料热容数据警告')).not.toBeInTheDocument()
    expect(screen.queryByText('物性待核实')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
    await waitFor(() => expect(api.generateTemplateModel).toHaveBeenCalledTimes(2))
    expect(vi.mocked(api.generateTemplateModel).mock.lastCall?.[0].custom_materials[0])
      .toMatchObject({ id: 'adhesive', density: 2200, specific_heat: 900 })
    expect(suspect.density).toBe(1)
    expect(suspect.specific_heat).toBe(1)
  })

  it('continues to show actual export failures', async () => {
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    vi.mocked(api.downloadTemplateModel).mockRejectedValueOnce(new Error('模型无效'))
    fireEvent.click(screen.getByRole('button', { name: '导出 FloXML' }))
    expect(await screen.findByText('模型无效')).toBeInTheDocument()
    expect(api.downloadTemplateModel).toHaveBeenCalledOnce()
  })
})
