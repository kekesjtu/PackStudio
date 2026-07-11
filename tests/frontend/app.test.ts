import { createElement } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../../src/frontend/App'
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
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => generatedModel }),
    )
  })

  afterEach(() => vi.unstubAllGlobals())

  it('renders the four-column workspace and generates the default model', async () => {
    render(createElement(App))

    expect(screen.getByRole('heading', { name: 'PackStudio' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: '封装结构属性' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '汇总' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '三维建模区' })).toBeInTheDocument()
    const resizer = screen.getByRole('separator', { name: '调整属性与三维视图宽度' })
    expect(resizer).toHaveAttribute('aria-valuenow', '380')
    fireEvent.keyDown(resizer, { key: 'ArrowRight' })
    expect(resizer).toHaveAttribute('aria-valuenow', '400')
    expect(screen.getByRole('tab', { name: '材料库' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '模型树' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '导出精简 PTA XML' })).toBeInTheDocument()
    expect(screen.getByText(/PTA 文件不包含网格和求解结果/)).toBeInTheDocument()

    expect(await screen.findByText('1 个块')).toBeInTheDocument()
    expect(screen.getByText('物理焊球')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: '模型树' }))
    expect(screen.getByText('Package substrate')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/templates/flip-chip-cbga/generate',
      expect.objectContaining({ method: 'POST' }),
    )
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
