import { createElement } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../../src/frontend/App'
import { createDefaultParameters } from '../../src/frontend/features/flip-chip-cbga/defaults'
import { applyPackagePreset } from '../../src/frontend/features/flip-chip-cbga/packagePresets'
import { saveParameters } from '../../src/frontend/features/flip-chip-cbga/parameterStorage'
import type { PackageModel } from '../../src/frontend/features/flip-chip-cbga/types'

vi.mock('../../src/frontend/features/flip-chip-cbga/ModelPreview', () => ({
  default: () => createElement('div', { 'aria-label': '测试三维模型' }),
}))

const generatedModel: PackageModel = {
  schema_version: 'packstudio.model/v1',
  template_id: 'flip-chip-cbga',
  name: 'Flip Chip CBGA',
  length_unit: 'mm',
  coordinate_system: {
    origin: 'substrate bottom-face center',
    x_axis: 'package length',
    y_axis: 'package width',
    z_axis: 'upward through package thickness',
  },
  materials: [
    {
      id: 'alumina',
      name: 'Alumina',
      conductivity: { x: 25, y: 25, z: 25 },
      density: 3900,
      specific_heat: 880,
      color: '#6975DC',
    },
  ],
  blocks: [
    {
      id: 'substrate',
      name: 'Package substrate',
      structure_type: 'substrate',
      origin: { x: -3, y: -3, z: 0 },
      size: { x: 6, y: 6, z: 1.15 },
      material_id: 'alumina',
      parent_group_id: 'substrate-group',
      metadata: {},
    },
  ],
  groups: [
    { id: 'package', name: 'Flip Chip CBGA', parent_id: null, block_ids: [] },
    {
      id: 'substrate-group',
      name: 'Substrate',
      parent_id: 'package',
      block_ids: ['substrate'],
    },
  ],
  heat_sources: [],
  boundaries: [],
  metadata: { solder_ball_count: 49 },
}

describe('Flip Chip CBGA workspace', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => generatedModel }),
    )
  })

  afterEach(() => {
    window.localStorage.clear()
    vi.unstubAllGlobals()
  })

  it('renders the four-column workspace and generates the default model', async () => {
    render(createElement(App))

    expect(screen.getByRole('heading', { name: 'PackStudio' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: '封装结构属性' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '汇总' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '三维建模区' })).toBeInTheDocument()
    const propertyResizer = screen.getByRole('separator', { name: '调整属性栏宽度' })
    const inspectorResizer = screen.getByRole('separator', { name: '调整检查器宽度' })
    expect(propertyResizer).toHaveAttribute('aria-valuenow', '380')
    expect(inspectorResizer).toHaveAttribute('aria-valuenow', '320')
    fireEvent.keyDown(propertyResizer, { key: 'ArrowRight' })
    fireEvent.keyDown(inspectorResizer, { key: 'ArrowLeft' })
    expect(propertyResizer).toHaveAttribute('aria-valuenow', '400')
    expect(inspectorResizer).toHaveAttribute('aria-valuenow', '340')
    expect(screen.getByRole('tab', { name: '材料库' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '模型树' })).toBeInTheDocument()
    const materialResizer = screen.getByRole('separator', {
      name: '调整材料列表和属性区域高度',
    })
    expect(materialResizer).toHaveAttribute('aria-valuenow', '240')
    fireEvent.keyDown(materialResizer, { key: 'ArrowDown' })
    expect(materialResizer).toHaveAttribute('aria-valuenow', '260')
    expect(screen.getByRole('button', { name: '保存参数' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '导出 PTA XML' })).toBeInTheDocument()
    expect(screen.queryByText(/PTA 文件不包含网格和求解结果/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '焊球样式' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '焊球去除' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '中央焊球' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '网格尺寸' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '边界条件' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '倒装芯片凸点' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: '基本尺寸预设' })).toHaveTextContent(
      'CBGAFC_49_6X6mm',
    )
    expect(screen.getByText(/切换预设会覆盖/)).toBeInTheDocument()

    expect(await screen.findByText('1 个块')).toBeInTheDocument()
    expect(screen.getByText('物理焊球')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: '模型树' }))
    expect(screen.getByText('Package substrate')).toBeInTheDocument()
    expect(screen.queryByText('substrate')).not.toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/templates/flip-chip-cbga/generate',
      expect.objectContaining({ method: 'POST' }),
    )
    const defaultBody = JSON.parse(String(vi.mocked(fetch).mock.calls[0][1]?.body)) as {
      solder_balls: {
        center_solder_enabled: boolean
        solder_removal_enabled: boolean
        matrix_material: { id: string }
        pattern?: string
      }
      flip_chip_bumps: { representation: string }
      mesh: { resolution: string }
    }
    expect(defaultBody.solder_balls.pattern).toBeUndefined()
    expect(defaultBody.solder_balls.center_solder_enabled).toBe(false)
    expect(defaultBody.solder_balls.solder_removal_enabled).toBe(false)
    expect(defaultBody.solder_balls.matrix_material.id).toBe('air')
    expect(defaultBody.flip_chip_bumps.representation).toBe('equivalent')
    expect(defaultBody.mesh.resolution).toBe('standard')

    fireEvent.click(screen.getByRole('button', { name: '倒装芯片凸点' }))
    expect(screen.getByText('凸点数量：49')).toBeInTheDocument()
    expect(screen.getByText('单元密度：16.00 个/mm²')).toBeInTheDocument()
    expect(screen.getByText('截面填充率：18.10%')).toBeInTheDocument()
    expect(screen.queryByText('凸块排列')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '边界条件' }))
    expect(screen.getByLabelText('PCB 侧对流换热系数')).toHaveValue(1600)
    expect(screen.getByLabelText('顶部对流换热系数')).toHaveValue(10)
    expect(screen.queryByText(/热阻/)).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '焊球样式' }))
    expect(screen.getByRole('checkbox', { name: '中央焊球' })).not.toBeChecked()
    expect(screen.getByRole('checkbox', { name: '焊球去除' })).not.toBeChecked()
    expect(screen.queryByText(/交错阵列|全阵列/)).not.toBeInTheDocument()
  })

  it('combines center solder with removal and sends both settings', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '焊球样式' }))
    fireEvent.click(screen.getByRole('checkbox', { name: '焊球去除' }))
    fireEvent.click(screen.getByRole('checkbox', { name: '中央焊球' }))

    expect(screen.getByLabelText('中央去球区行数')).toHaveValue(5)
    expect(screen.getByLabelText('中央焊球行数')).toHaveValue(3)
    expect(screen.getByText(/中央焊球会在中央去球区内重新加入/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    const body = JSON.parse(String(vi.mocked(fetch).mock.calls[1][1]?.body)) as {
      solder_balls: {
        center_solder_enabled: boolean
        solder_removal_enabled: boolean
        center_solder_rows: number
        removal_rows: number
      }
    }
    expect(body.solder_balls).toMatchObject({
      center_solder_enabled: true,
      solder_removal_enabled: true,
      center_solder_rows: 3,
      removal_rows: 5,
    })
  })

  it('applies a footprint preset and saves it in the browser', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    const presetSelect = screen.getByRole('combobox', { name: '基本尺寸预设' })
    fireEvent.mouseDown(presetSelect)
    fireEvent.click(await screen.findByRole('option', { name: 'CBGAFC_64_7X7mm' }))
    expect(presetSelect).toHaveTextContent('CBGAFC_64_7X7mm')

    fireEvent.click(screen.getByRole('button', { name: '保存参数' }))
    expect(window.localStorage.getItem('packstudio.flip-chip-cbga.parameters.v1')).not.toBeNull()
    expect(screen.getByText('参数已保存')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    const body = JSON.parse(String(vi.mocked(fetch).mock.calls[1][1]?.body)) as {
      substrate: { length: number }
      solder_balls: { rows: number; columns: number }
    }
    expect(body.substrate.length).toBe(7)
    expect(body.solder_balls).toMatchObject({ rows: 8, columns: 8 })
  })

  it('restores explicitly saved parameters on the next page load', async () => {
    const saved = applyPackagePreset(createDefaultParameters(), 'cbgafc-64-7x7')
    saveParameters(saved)

    render(createElement(App))
    await screen.findByText('1 个块')

    expect(screen.getByRole('combobox', { name: '基本尺寸预设' })).toHaveTextContent(
      'CBGAFC_64_7X7mm',
    )
    const body = JSON.parse(String(vi.mocked(fetch).mock.calls[0][1]?.body)) as {
      substrate: { length: number; width: number }
      solder_balls: { rows: number; columns: number }
    }
    expect(body.substrate).toMatchObject({ length: 7, width: 7 })
    expect(body.solder_balls).toMatchObject({ rows: 8, columns: 8 })
    expect(screen.getByText('参数已保存')).toBeInTheDocument()
  })

  it('enables encapsulant parameters and supports model-tree visibility actions', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '塑封' }))
    fireEvent.click(screen.getByRole('switch', { name: '包含塑封' }))
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    const request = vi.mocked(fetch).mock.calls[1]
    const body = JSON.parse(String(request[1]?.body)) as { encapsulant: { enabled: boolean } }
    expect(body.encapsulant.enabled).toBe(true)

    fireEvent.click(screen.getByRole('tab', { name: '模型树' }))
    fireEvent.contextMenu(screen.getByRole('button', { name: /Package substrate/ }))
    fireEvent.click(screen.getByRole('menuitem', { name: '隐藏这个模型' }))
    expect(screen.getByText('隐藏 1')).toBeInTheDocument()
  })

  it('shows backend validation errors without hiding the workspace', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({ detail: '焊球直径必须小于 pitch' }),
    } as Response)

    render(createElement(App))

    expect(await screen.findByText('焊球直径必须小于 pitch')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '三维建模区' })).toBeInTheDocument()
  })
})
