import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import materialQuality from '../../src/frontend/features/model-editor/materialQuality'
import MaterialFields from '../../src/frontend/features/model-editor/MaterialFields'
import MaterialLibraryBrowser from '../../src/frontend/features/package-library/MaterialLibraryBrowser'
import requestMaterialWarnings from '../../src/frontend/features/package-library/requestMaterialWarnings'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import { model, request, safe, selection, suspect } from './materialQualityFixtures'

describe('material heat-capacity data warnings', () => {
  it('identifies each exact placeholder property without changing the material', () => {
    const before = structuredClone(suspect)
    expect(materialQuality(suspect)?.properties).toHaveLength(2)
    expect(materialQuality({ ...safe, density: 1 })?.properties).toEqual(['密度 = 1 kg/m³'])
    expect(materialQuality({ ...safe, specific_heat: 1 })?.properties).toEqual(['比热 = 1 J/(kg·K)'])
    expect(materialQuality({ ...safe, density: 1.165 })).toBeNull()
    expect(suspect).toEqual(before)
  })

  it('uses preset selections and active conditions, excluding unused catalog entries', () => {
    expect(requestMaterialWarnings([], request, [suspect, safe], model)).toEqual([])
    expect(requestMaterialWarnings([selection], request, [suspect], null)).toHaveLength(1)
    const preset = { ...selection, target_id: 'sample.footprint', control: 'footprint',
      default: 'preset', preset_values: { preset: {} },
      preset_materials: { preset: { 'group-adhesive': 'safe' } } }
    expect(requestMaterialWarnings([selection, preset], request, [suspect, safe], null)).toEqual([])
    expect(requestMaterialWarnings([{ ...selection, visible_when: { enabled: true } }],
      request, [suspect], null)).toEqual([])
    expect(requestMaterialWarnings([{ ...selection, enabled_when: { enabled: true } }],
      request, [suspect], null)).toEqual([])
    expect(requestMaterialWarnings([{ ...selection, hidden_when: {} }],
      request, [suspect], null)).toEqual([])
  })

  it('clears only corrected properties using the last design override', () => {
    const corrected = { ...safe, id: suspect.id }
    const partial = { ...corrected, specific_heat: 1 }
    expect(requestMaterialWarnings([selection], { ...request, custom_materials: [partial] },
      [suspect], null)[0].properties).toEqual(['比热 = 1 J/(kg·K)'])
    expect(requestMaterialWarnings([selection], { ...request,
      custom_materials: [partial, corrected] }, [suspect], null)).toEqual([])
  })

  it('retains constituent warnings for derived values that are not 1 and handles cycles', () => {
    const equivalent = { ...safe, source: 'PACK derived mixture; metal=adhesive; matrix=safe;' }
    const result = requestMaterialWarnings([], request, [suspect, equivalent],
      { ...model, materials: [equivalent, { ...suspect, id: 'unused' }] })
    expect(result.map((issue) => issue.material.id)).toEqual(['adhesive'])
  })

  it.each(['cbga_fc', 'pbga_fc', 'bare_die'])('tracks hidden underfill before generation in %s', (templateId) => {
    const underfill = { ...suspect, id: 'underfill' }
    const enabled = { ...selection, control: 'checkbox', property_name: 'bumps.enabled', default: true }
    const current = { ...request, template_id: templateId }
    expect(requestMaterialWarnings([enabled], current, [underfill], null))
      .toEqual([materialQuality(underfill)])
    expect(requestMaterialWarnings([enabled], { ...current,
      custom_materials: [{ ...safe, id: 'underfill' }] }, [underfill], null)).toEqual([])
  })

  it('does not warn for unused underfill on Bare Die with bumps disabled', () => {
    const disabled = { ...selection, control: 'checkbox', property_name: 'bumps.enabled', default: false }
    expect(requestMaterialWarnings([disabled], { ...request, template_id: 'bare_die' },
      [{ ...suspect, id: 'underfill' }], null)).toEqual([])
  })

  it('tracks fixed BGA constituents before generation and from actual equivalent materials', () => {
    const solder = { ...suspect, id: 'solder-sn63' }
    expect(requestMaterialWarnings([], { ...request, bga: { representation: 'equivalent',
      center_solder_enabled: false, center_solder_rows: 1, center_solder_columns: 1,
      solder_removal_enabled: false, removal_rows: 0, removal_columns: 0, omitted_cells: [],
    } }, [solder], null)).toEqual([materialQuality(solder)])
    const id = 'solder-ball-equivalent'
    expect(requestMaterialWarnings([], request, [solder], { ...model,
      materials: [{ ...safe, id }], blocks: [{ ...model.blocks[0], material_id: id }],
    })).toEqual([materialQuality(solder)])
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
