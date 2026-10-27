import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import ModelTree from '../../src/frontend/features/model-editor/ModelTree'
import type {
  AxisAlignedBlock,
  PackageModel,
} from '../../src/frontend/features/model-editor/types'

const blocks: AxisAlignedBlock[] = [
  block('die-block', 'Die block', 'group-die'),
  block('attach-block', 'Die attach block', 'group-die-attach'),
]

const model: PackageModel = {
  schema_version: 'packstudio.model/v1',
  template_id: 'test',
  name: 'Test package',
  length_unit: 'mm',
  coordinate_system: {
    origin: 'package bottom center',
    x_axis: '+X',
    y_axis: '+Y',
    z_axis: '+Z',
  },
  materials: [],
  blocks,
  groups: [
    {
      id: 'package',
      name: 'Test package',
      parent_id: null,
      block_ids: [],
    },
    {
      id: 'group-die',
      name: 'Die assembly',
      parent_id: 'package',
      block_ids: ['die-block'],
    },
    {
      id: 'group-die-attach',
      name: 'Die attach',
      parent_id: 'group-die',
      block_ids: ['attach-block'],
    },
  ],
  heat_sources: [],
  boundaries: [],
  metadata: {},
}

function renderTree(treeModel = model, hiddenBlockIds = new Set<string>()) {
  const onSetBlockHidden = vi.fn()
  const onShowOnlyBlock = vi.fn()
  const onShowAllBlocks = vi.fn()
  const onSelectBlock = vi.fn()
  render(
    <ModelTree
      model={treeModel}
      selectedBlockId={null}
      hiddenBlockIds={hiddenBlockIds}
      onSelectBlock={onSelectBlock}
      onSetBlockHidden={onSetBlockHidden}
      onShowOnlyBlock={onShowOnlyBlock}
      onShowAllBlocks={onShowAllBlocks}
    />,
  )
  return { onSetBlockHidden, onShowOnlyBlock, onShowAllBlocks, onSelectBlock }
}

describe('ModelTree', () => {
  it('uses one ordinary tree without component/layer view tabs', () => {
    renderTree()

    expect(screen.queryByRole('button', { name: '组件层级' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Layer 层级' })).not.toBeInTheDocument()
    expect(screen.getByText('Die block')).toBeInTheDocument()
  })

  it('collapses and expands parent nodes', () => {
    renderTree()

    fireEvent.click(screen.getByRole('button', { name: '折叠 Die assembly' }))
    expect(screen.queryByText('Die block')).not.toBeInTheDocument()
    expect(screen.queryByText('Die attach')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '展开 Die assembly' }))
    expect(screen.getByText('Die block')).toBeInTheDocument()
    expect(screen.getByText('Die attach')).toBeInTheDocument()
  })

  it('collapses and expands the complete tree with one toolbar button', () => {
    renderTree()

    fireEvent.click(screen.getByRole('button', { name: '全部折叠' }))
    expect(screen.queryByText('Die assembly')).not.toBeInTheDocument()
    expect(screen.queryByText('Die block')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '全部展开' }))
    expect(screen.getByText('Die assembly')).toBeInTheDocument()
    expect(screen.getByText('Die block')).toBeInTheDocument()
  })

  it('applies parent visibility changes to every descendant block', () => {
    const { onSetBlockHidden } = renderTree()

    expect(screen.queryByRole('button', { name: '隐藏 Die assembly' })).not.toBeInTheDocument()
    fireEvent.contextMenu(screen.getByRole('button', { name: '折叠 Die assembly' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '隐藏这个分组' }))

    expect(onSetBlockHidden).toHaveBeenCalledTimes(2)
    expect(onSetBlockHidden).toHaveBeenNthCalledWith(1, 'die-block', true)
    expect(onSetBlockHidden).toHaveBeenNthCalledWith(2, 'attach-block', true)
  })

  it('shows all descendants of a hidden collapsed group from its context menu', () => {
    const { onSetBlockHidden } = renderTree(model, new Set(['die-block', 'attach-block']))
    fireEvent.click(screen.getByRole('button', { name: '折叠 Die assembly' }))
    fireEvent.contextMenu(screen.getByRole('button', { name: '展开 Die assembly' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '显示这个分组' }))
    expect(onSetBlockHidden.mock.calls).toEqual([['die-block', false], ['attach-block', false]])
  })

  it('hides a partially visible group and isolates the full group recursively', () => {
    const other = block('other', 'Other', 'package')
    const { onSetBlockHidden } = renderTree({ ...model,
      blocks: [...model.blocks, other],
      groups: model.groups.map((group) => group.id === 'package'
        ? { ...group, block_ids: ['other'] } : group),
    }, new Set(['die-block']))
    fireEvent.contextMenu(screen.getByRole('button', { name: '折叠 Die assembly' }))
    expect(screen.getByRole('menuitem', { name: '隐藏这个分组' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('menuitem', { name: '只显示这个分组' }))
    expect(onSetBlockHidden.mock.calls).toEqual([
      ['die-block', false], ['attach-block', false], ['other', true],
    ])
  })

  it('keeps left clicks for selection and uses the block context menu for visibility', () => {
    const { onSelectBlock, onSetBlockHidden, onShowOnlyBlock } = renderTree()
    fireEvent.click(screen.getByRole('button', { name: 'Die block' }))
    expect(onSelectBlock).toHaveBeenCalledWith('die-block')
    expect(onSetBlockHidden).not.toHaveBeenCalled()
    fireEvent.contextMenu(screen.getByRole('button', { name: 'Die block' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '隐藏这个模型' }))
    expect(onSetBlockHidden).toHaveBeenCalledWith('die-block', true)
    fireEvent.contextMenu(screen.getByRole('button', { name: 'Die block' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '只显示这个模型' }))
    expect(onShowOnlyBlock).toHaveBeenCalledWith('die-block')
  })

  it('opens global visibility actions on the blank tree area', () => {
    const { onSetBlockHidden, onShowAllBlocks } = renderTree()
    fireEvent.contextMenu(screen.getByRole('region', { name: '模型树' }))
    expect(screen.queryByRole('menuitem', { name: '隐藏这个模型' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('menuitem', { name: '隐藏全部模型' }))
    expect(onSetBlockHidden.mock.calls).toEqual([['die-block', true], ['attach-block', true]])
    fireEvent.contextMenu(screen.getByRole('region', { name: '模型树' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '显示全部模型' }))
    expect(onShowAllBlocks).toHaveBeenCalledOnce()
  })

  it('sorts groups and direct blocks together from high Z to low Z while preserving hierarchy', () => {
    const stacked = structuredClone(model)
    stacked.blocks[0].origin.z = 1
    stacked.blocks[1].origin.z = 10
    const substrate = block('substrate', 'Substrate block', 'substrate-group')
    substrate.origin.z = -5
    stacked.blocks.push(substrate)
    stacked.groups.splice(1, 0,
      { id: 'empty', name: 'Empty', parent_id: 'package', block_ids: [] },
      { id: 'substrate-group', name: 'Substrate', parent_id: 'package', block_ids: ['substrate'] })
    const before = structuredClone(stacked)
    renderTree(stacked)
    expect(screen.getAllByRole('button').map((button) => button.textContent)).toEqual([
      '⊟全部折叠', '−Test package', '−Die assembly', '−Die attach',
      'Die attach block', 'Die block', '−Substrate', 'Substrate block', '−Empty',
    ])
    expect(stacked).toEqual(before)
  })
})

function block(id: string, name: string, parentGroupId: string): AxisAlignedBlock {
  return {
    id,
    name,
    structure_type: 'die',
    origin: { x: 0, y: 0, z: 0 },
    size: { x: 1, y: 1, z: 1 },
    material_id: 'silicon',
    parent_group_id: parentGroupId,
    metadata: {},
  }
}
