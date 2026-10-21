import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import ViaRemovalPanel from '../../src/frontend/features/package-library/ViaRemovalPanel'
import { restoreTemplateRequest, saveTemplateRequest } from '../../src/frontend/features/package-library/requestStorage'
import { pruneViaConfiguration, viaDimensions } from '../../src/frontend/features/package-library/viaConfiguration'
import type { TemplateRequest, TemplateSchema, ViaConfiguration, WizardField } from '../../src/frontend/features/package-library/types'

const value: ViaConfiguration = {
  removal_enabled: true, removal_rows: 1, removal_columns: 1, omitted_cells: [],
}

function field(property: string, initial: number | boolean): WizardField {
  return {
    target_id: `qfn.${property}`, property_name: property, label: property,
    default: initial, options: [], supported_values: [], control: 'number',
    component: null, ui_location: 'thermal_vias', classification: 'numeric_parameter',
    evidence_status: 'implemented', editable: true,
  }
}
const fields = [field('vias.rows', 3), field('vias.columns', 4), field('vias.enabled', true)]
const request: TemplateRequest = {
  template_id: 'qfn', design_name: null, bga: null, overrides: {},
  material_assignments: {}, custom_materials: [], die_power_w: null,
  mesh: { resolution: 'standard' }, vias: value,
}
const schema: TemplateSchema = {
  schema_version: 'packstudio.wizard/v2', template_id: 'qfn', has_bga: false,
  steps: [{ id: 'thermal_vias', label: '热通孔', fields }],
  special_rules: { outline_type: 'standard_outline', die_type: 'actual_type', bga_pattern: null, flip_chip_bumps: null },
}

describe('thermal via removal', () => {
  it('reuses the matrix with via labels and independent cell selection', () => {
    const onChange = vi.fn()
    render(<ViaRemovalPanel value={value} enabled rows={3} columns={3} onChange={onChange} />)
    expect(screen.getByRole('button', { name: '行 1，列 1，已被去孔区覆盖' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: '行 0，列 2，添加显式去孔' }))
    expect(onChange.mock.calls[0][0]).toEqual({ ...value, omitted_cells: [{ row: 0, column: 2 }] })
  })

  it('hides controls while vias are disabled and clears explicit cells when removal is disabled', () => {
    const onChange = vi.fn()
    const { rerender } = render(<ViaRemovalPanel value={value} enabled={false} rows={3} columns={3} onChange={onChange} />)
    expect(screen.queryByRole('group', { name: /去孔矩阵/ })).not.toBeInTheDocument()
    rerender(<ViaRemovalPanel value={{ ...value, omitted_cells: [{ row: 0, column: 0 }] }} enabled rows={3} columns={3} onChange={onChange} />)
    fireEvent.click(screen.getByRole('switch', { name: '热通孔去除' }))
    expect(onChange.mock.calls[0][0].removal_enabled).toBe(false)
    expect(onChange.mock.calls[0][0].omitted_cells).toEqual([])
  })

  it('restores saved via cells and upgrades older saved requests', () => {
    const saved = { ...request, vias: { ...value, omitted_cells: [{ row: 2, column: 3 }] } }
    saveTemplateRequest('qfn', saved)
    expect(restoreTemplateRequest('qfn', request, schema)?.vias).toEqual(saved.vias)
    const older = { ...request }
    delete older.vias
    saveTemplateRequest('qfn', older)
    expect(restoreTemplateRequest('qfn', request, schema)?.vias).toEqual(value)
  })

  it('uses Chip Array solder dimensions and removes stale cells after shrinking arrays', () => {
    const chipFields = [field('bga.rows', 3), field('bga.columns', 4)]
    expect(viaDimensions(chipFields, request)).toEqual({ rows: 3, columns: 4 })
    const saved = { ...request, overrides: { 'qfn.vias.rows': 2, 'qfn.vias.columns': 2 },
      vias: { ...value, removal_rows: 3, removal_columns: 4,
        omitted_cells: [{ row: 0, column: 0 }, { row: 2, column: 3 }] } }
    expect(pruneViaConfiguration(saved, fields).vias).toEqual({
      ...value, removal_rows: 2, removal_columns: 2, omitted_cells: [{ row: 0, column: 0 }],
    })
  })
})
