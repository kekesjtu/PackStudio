import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../../src/frontend/features/package-library/api'
import PackageWorkspace from '../../src/frontend/features/package-library/PackageWorkspace'
import { model, request, safe, schema, suspect } from './materialQualityFixtures'

vi.mock('../../src/frontend/features/package-library/api')
vi.mock('../../src/frontend/features/model-editor/ModelPreview', () => ({ default: () => null }))

beforeEach(() => {
  vi.resetAllMocks()
  localStorage.clear()
  vi.mocked(api.loadTemplateSchema).mockResolvedValue(schema)
  vi.mocked(api.loadTemplateDefaults).mockResolvedValue(request)
  vi.mocked(api.loadTemplateMaterials).mockResolvedValue([safe, suspect])
  vi.mocked(api.generateTemplateModel).mockResolvedValue(model)
  vi.mocked(api.downloadTemplateModel).mockResolvedValue()
})

describe('workspace material warnings and export preflight', () => {
  it('warns on initial inputs and after saved designs are restored', async () => {
    localStorage.setItem('packstudio.library.v3.sample', JSON.stringify(request))
    render(<PackageWorkspace templateId="sample" />)
    expect(await screen.findByText('参数已保存')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('芯片胶（adhesive）')
    expect(screen.getByRole('alert')).toHaveTextContent('瞬态分析')
    expect(api.generateTemplateModel).toHaveBeenCalledWith(request)
    expect(api.downloadTemplateModel).not.toHaveBeenCalled()
  })

  it.each([
    ['pta', 'PTA XML'], ['ecxml', 'ECXML'], ['floxml', 'FloXML（FloTHERM）'],
  ] as const)('checks current material data before %s download, including dirty designs', async (format, label) => {
    vi.mocked(api.loadTemplateSchema).mockResolvedValue({ ...schema, steps: [] })
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('设计名称'), { target: { value: '当前修改' } })
    const generated = { ...model, materials: [{ ...safe,
      source: 'PACK derived mixture; metal=adhesive; matrix=safe;' }] }
    vi.mocked(api.generateTemplateModel).mockResolvedValueOnce(generated)
    if (format !== 'pta') {
      fireEvent.mouseDown(screen.getByLabelText('导出格式'))
      fireEvent.click(screen.getByRole('option', { name: label }))
    }
    fireEvent.click(screen.getByRole('button', { name: /^导出 / }))
    await waitFor(() => expect(api.downloadTemplateModel).toHaveBeenCalledOnce())
    expect(api.generateTemplateModel).toHaveBeenLastCalledWith({ ...request, design_name: '当前修改' })
    expect(api.downloadTemplateModel).toHaveBeenCalledWith({ ...request, design_name: '当前修改' }, format)
    expect(api.generateTemplateModel.mock.invocationCallOrder.at(-1)!)
      .toBeLessThan(api.downloadTemplateModel.mock.invocationCallOrder[0])
    expect(screen.getByText('材料热容数据警告').closest('[role="alert"]'))
      .toHaveTextContent('芯片胶（adhesive）')
  })

  it('removes current-input warnings after both properties are corrected', async () => {
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    fireEvent.click(screen.getByRole('button', { name: /芯片胶.*adhesive/ }))
    fireEvent.change(screen.getByLabelText('密度'), { target: { value: '2200' } })
    fireEvent.change(screen.getByLabelText('比热'), { target: { value: '900' } })
    expect(screen.queryByText('材料热容数据警告')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
    await waitFor(() => expect(api.generateTemplateModel).toHaveBeenCalledTimes(2))
    expect(vi.mocked(api.generateTemplateModel).mock.lastCall?.[0].custom_materials[0])
      .toMatchObject({ id: 'adhesive', density: 2200, specific_heat: 900 })
    expect(suspect.density).toBe(1)
    expect(suspect.specific_heat).toBe(1)
  })

  it('does not download if preflight generation fails', async () => {
    render(<PackageWorkspace templateId="sample" />)
    await screen.findByText('1 个块')
    vi.mocked(api.generateTemplateModel).mockRejectedValueOnce(new Error('模型无效'))
    fireEvent.click(screen.getByRole('button', { name: '导出 PTA XML' }))
    expect(await screen.findByText('模型无效')).toBeInTheDocument()
    expect(api.downloadTemplateModel).not.toHaveBeenCalled()
  })
})
