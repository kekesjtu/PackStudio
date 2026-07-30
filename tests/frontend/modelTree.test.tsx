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

function renderTree() {
  const onSetBlockHidden = vi.fn()
  render(
    <ModelTree
      model={model}
      selectedBlockId={null}
      hiddenBlockIds={new Set()}
      onSelectBlock={vi.fn()}
      onSetBlockHidden={onSetBlockHidden}
      onShowOnlyBlock={vi.fn()}
      onShowAllBlocks={vi.fn()}
    />,
  )
  return { onSetBlockHidden }
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

    fireEvent.click(screen.getByRole('button', { name: '隐藏 Die assembly' }))

    expect(onSetBlockHidden).toHaveBeenCalledTimes(2)
    expect(onSetBlockHidden).toHaveBeenNthCalledWith(1, 'die-block', true)
    expect(onSetBlockHidden).toHaveBeenNthCalledWith(2, 'attach-block', true)
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
