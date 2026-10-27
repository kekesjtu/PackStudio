import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ModelTree from '../../src/frontend/features/model-editor/ModelTree'
import { model as baseModel } from './materialQualityFixtures'

const model = { ...baseModel,
  blocks: [1, 2, 3, 4, 5].map((z) => ({ ...baseModel.blocks[0], id: `b${z}`, name: `Block ${z}`,
    origin: { x: 0, y: 0, z }, parent_group_id: z === 3 || z === 4 ? 'inner' : 'package' })),
  groups: [
    { id: 'package', name: 'Package', parent_id: null, block_ids: ['b1', 'b2', 'b5'] },
    { id: 'inner', name: 'Inner', parent_id: 'package', block_ids: ['b3', 'b4'] },
  ],
}

function setup() {
  const onSelect = vi.fn()
  const onHidden = vi.fn()
  const onShowOnly = vi.fn()
  function Tree() {
    const [selected, setSelected] = useState<Set<string>>(() => new Set())
    const [hidden, setHidden] = useState<Set<string>>(() => new Set())
    return <ModelTree model={model} selectedBlockIds={selected} hiddenBlockIds={hidden}
      onSelectBlocks={(ids) => { setSelected(new Set(ids)); onSelect(ids) }}
      onSetBlockHidden={(id, value) => {
        onHidden(id, value)
        setHidden((current) => { const next = new Set(current); if (value) next.add(id); else next.delete(id); return next })
      }} onShowOnlyBlock={onShowOnly} onShowAllBlocks={() => setHidden(new Set())} />
  }
  render(<Tree />)
  return { onSelect, onHidden, onShowOnly }
}
const row = (n: number) => screen.getByRole('button', { name: new RegExp(`^Block ${n}(\\s*已隐藏)?$`) })
const selected = () => screen.getAllByRole('button', { pressed: true }).map((button) => button.textContent)

describe('model tree block selection', () => {
  it('uses ordinary click to replace selection and Ctrl to add or remove individual blocks', () => {
    setup()
    fireEvent.click(row(5))
    fireEvent.click(row(2), { ctrlKey: true })
    expect(selected()).toEqual(['Block 5', 'Block 2'])
    fireEvent.click(row(5), { ctrlKey: true })
    expect(selected()).toEqual(['Block 2'])
    fireEvent.click(row(1))
    expect(selected()).toEqual(['Block 1'])
  })

  it('selects a reversible range in displayed Z order and combines it with Ctrl+Shift', () => {
    setup()
    fireEvent.click(row(2))
    fireEvent.click(row(5), { shiftKey: true })
    expect(selected()).toEqual(['Block 5', 'Block 4', 'Block 3', 'Block 2'])
    fireEvent.click(row(3), { shiftKey: true })
    expect(selected()).toEqual(['Block 3', 'Block 2'])
    fireEvent.click(row(1), { ctrlKey: true })
    fireEvent.click(row(4), { ctrlKey: true, shiftKey: true })
    expect(selected()).toEqual(['Block 4', 'Block 3', 'Block 2', 'Block 1'])
  })

  it('ranges over visible rows and falls back to one block when the anchor is collapsed', () => {
    setup()
    fireEvent.click(row(5))
    fireEvent.click(screen.getByRole('button', { name: '折叠 Inner' }))
    fireEvent.click(row(1), { shiftKey: true })
    expect(selected()).toEqual(['Block 5', 'Block 2', 'Block 1'])
    fireEvent.click(screen.getByRole('button', { name: '展开 Inner' }))
    fireEvent.click(row(3))
    fireEvent.click(screen.getByRole('button', { name: '折叠 Inner' }))
    fireEvent.click(row(2), { shiftKey: true })
    expect(selected()).toEqual(['Block 2'])
  })

  it('applies the context menu to all selected blocks and isolates an unselected right-click target', () => {
    const { onHidden, onShowOnly } = setup()
    fireEvent.click(row(5))
    fireEvent.click(row(2), { ctrlKey: true })
    fireEvent.contextMenu(row(5))
    fireEvent.click(screen.getByRole('menuitem', { name: '隐藏所选模型' }))
    expect(onHidden.mock.calls).toEqual([['b2', true], ['b5', true]])
    fireEvent.contextMenu(row(5))
    fireEvent.click(screen.getByRole('menuitem', { name: '显示所选模型' }))
    fireEvent.contextMenu(row(2))
    fireEvent.click(screen.getByRole('menuitem', { name: '只显示所选模型' }))
    expect(onHidden.mock.calls.slice(-5)).toEqual([
      ['b1', true], ['b2', false], ['b3', true], ['b4', true], ['b5', false],
    ])
    fireEvent.contextMenu(row(3))
    fireEvent.click(screen.getByRole('menuitem', { name: '只显示这个模型' }))
    expect(onShowOnly).toHaveBeenCalledWith('b3')
  })
})
