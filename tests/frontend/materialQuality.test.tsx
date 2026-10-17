import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import materialQuality from '../../src/frontend/features/model-editor/materialQuality'
import MaterialFields from '../../src/frontend/features/model-editor/MaterialFields'
import MaterialLibraryBrowser from '../../src/frontend/features/package-library/MaterialLibraryBrowser'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import { request, safe, selection, suspect } from './materialQualityFixtures'

describe('material heat-capacity data warnings', () => {
  it('identifies each exact placeholder property without changing the material', () => {
    const before = structuredClone(suspect)
    expect(materialQuality(suspect)?.properties).toHaveLength(2)
    expect(materialQuality({ ...safe, density: 1 })?.properties).toEqual(['密度 = 1 kg/m³'])
    expect(materialQuality({ ...safe, specific_heat: 1 })?.properties).toEqual(['比热 = 1 J/(kg·K)'])
    expect(materialQuality({ ...safe, density: 1.165 })).toBeNull()
    expect(suspect).toEqual(before)
  })

  it('keeps material editing compact without long warning paragraphs', () => {
    const onChange = vi.fn()
    const { rerender } = render(<MaterialFields material={suspect} onChange={onChange} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByLabelText('密度')).toHaveValue(1)
    expect(screen.getByLabelText('比热')).toHaveValue(1)
    fireEvent.change(screen.getByLabelText('密度'), { target: { value: '2200' } })
    expect(onChange.mock.calls[0][0]).toMatchObject({ density: 2200, specific_heat: 1 })
    rerender(<MaterialFields material={safe} onChange={onChange} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('keeps only the compact library tag and clears it when corrected', () => {
    const { rerender } = render(<MaterialLibraryBrowser materials={[suspect]} onChange={vi.fn()} />)
    expect(screen.getByText('物性待核实')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    rerender(<MaterialLibraryBrowser materials={[{ ...safe, id: suspect.id }]} onChange={vi.fn()} />)
    expect(screen.queryByText('物性待核实')).not.toBeInTheDocument()
  })

  it('tags selected materials and dropdown options without warning paragraphs', () => {
    const onChange = vi.fn()
    const { rerender } = render(<WizardFields step={{ id: 'adhesive', label: '胶', fields: [selection] }}
      allFields={[selection]} request={request} materials={[safe, suspect]} onChange={onChange} />)
    const select = screen.getByRole('combobox', { name: '芯片胶材料' })
    expect(select).toHaveTextContent('芯片胶')
    expect(within(select).getByText('物性待核实')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    fireEvent.mouseDown(select)
    expect(screen.getByRole('option', { name: '芯片胶 物性待核实' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '已补齐材料' })).not.toHaveTextContent('物性待核实')
    fireEvent.click(screen.getByRole('option', { name: '已补齐材料' }))
    rerender(<WizardFields step={{ id: 'adhesive', label: '胶', fields: [selection] }}
      allFields={[selection]} request={onChange.mock.calls[0][0]}
      materials={[safe, suspect]} onChange={onChange} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: '芯片胶材料' })).not.toHaveTextContent('物性待核实')
    expect(onChange.mock.calls[0][0].material_assignments).toEqual({ 'group-adhesive': 'safe' })
  })
})
