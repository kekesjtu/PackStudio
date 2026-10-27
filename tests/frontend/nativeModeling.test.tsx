import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import MetalLayerTable from '../../src/frontend/features/package-library/MetalLayerTable'
import NativeBgaPanel from '../../src/frontend/features/package-library/NativeBgaPanel'
import SolderBallMap from '../../src/frontend/features/package-library/SolderBallMap'
import updateWizardRequest from '../../src/frontend/features/package-library/updateWizardRequest'
import { valueFor } from '../../src/frontend/features/package-library/wizardValues'
import type { BgaConfiguration, TemplateRequest, WizardField, WizardValue } from '../../src/frontend/features/package-library/types'

const bga: BgaConfiguration = {
  representation: 'equivalent', center_solder_enabled: false,
  center_solder_rows: null, center_solder_columns: null, solder_removal_enabled: false,
  removal_rows: null, removal_columns: null, omitted_cells: [],
}

describe('native package modeling controls', () => {
  it('keeps a cleared metal thickness blank and preserves the other table values', () => {
    const onChange = vi.fn()
    render(<MetalLayerTable label="金属层" enabled
      value={'[{"depth":0.07,"thickness":0.018,"coverage":90}]'} onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('金属层 第 1 行 thickness'), { target: { value: '' } })
    expect(JSON.parse(onChange.mock.calls[0][0])).toEqual([
      { depth: 0.07, thickness: null, coverage: 90 },
    ])
  })

  it('keeps explicit cell editing independent of central removal and selects discrete balls', () => {
    const onChange = vi.fn()
    render(<NativeBgaPanel section="removal" rows={5} columns={5}
      value={{ ...bga, depopulated_center: true, solder_removal_enabled: true,
        populated_rows: 2, populated_columns: 2 }} onChange={onChange} />)
    expect(screen.getByLabelText('外围满布行数 MEp')).toHaveValue(2)
    fireEvent.click(screen.getByRole('button', { name: '行 2，列 2，添加显式去球' }))
    expect(onChange.mock.calls[0][0]).toMatchObject({
      depopulated_center: true, populated_rows: 2, populated_columns: 2,
      representation: 'discrete', omitted_cells: [{ row: 2, column: 2 }],
    })
  })

  it('imports CSV coordinates without merging coincident balls and reports duplicate IDs', () => {
    const onChange = vi.fn()
    render(<SolderBallMap value={{ ...bga, ball_map_enabled: true }} onChange={onChange} />)
    const input = screen.getByLabelText('ID, X (mm), Y (mm)')
    fireEvent.change(input, { target: { value: 'ID,X,Y\nA,-1.1,0.3\nB,0.25,-0.7\nC,0.25,-0.7' } })
    expect(onChange.mock.calls[0][0]).toMatchObject({ representation: 'discrete', ball_map: [
      { id: 'A', x: -1.1, y: 0.3 }, { id: 'B', x: 0.25, y: -0.7 }, { id: 'C', x: 0.25, y: -0.7 },
    ] })
    fireEvent.change(input, { target: { value: 'A,1,2\nA,3,4' } })
    expect(screen.getByText(/ID 必须唯一/)).toBeInTheDocument()
    expect(onChange).toHaveBeenCalledOnce()
  })

  it('keeps four-layer initialization and outer thicknesses consistent across footprint changes', () => {
    const field = (key: string, value: WizardValue, control = 'number'): WizardField => ({
      target_id: 'chip_array.' + key, property_name: key, label: key, default: value, control,
      ui_location: 'package', component: 'package', options: [], supported_values: [],
      classification: 'numeric_parameter', evidence_status: 'implemented', editable: true,
    })
    const layerField = field('substrate.layers', '2-Layer', 'select')
    const table = field('metal.layers', '[{"depth":0,"thickness":0.018,"coverage":20},{"depth":0.342,"thickness":0.018,"coverage":10}]', 'table')
    const footprint = { ...field('footprint.size', 'A', 'footprint'), options: ['A', 'B'],
      preset_values: { B: { 'chip_array.substrate.thickness': 0.36, 'chip_array.metal.layers': table.default } } }
    const top = field('trace.top_thickness', 0.018), bottom = field('trace.bottom_thickness', 0.018)
    const fields = [footprint, layerField, table, top, bottom, field('substrate.thickness', 0.36)]
    const initial: TemplateRequest = { template_id: 'chip_array', design_name: null,
      overrides: {}, material_assignments: {}, custom_materials: [], bga, die_power_w: null }
    const four = updateWizardRequest(initial, layerField, '4-Layer', fields)
    const changed = updateWizardRequest(four, footprint, 'B', fields)
    expect(changed.overrides['chip_array.substrate.thickness']).toBe(0.56)
    expect(JSON.parse(String(valueFor(table, changed, fields)))).toHaveLength(4)
    const thicker = updateWizardRequest(changed, top, 0.025, fields)
    expect(JSON.parse(String(valueFor(table, thicker, fields)))[0].thickness).toBe(0.025)
    const edited = updateWizardRequest(thicker, table,
      '[{"depth":0,"thickness":0.03,"coverage":20},{"depth":0.52,"thickness":0.04,"coverage":10}]', fields)
    expect(valueFor(top, edited, fields)).toBe(0.03)
    expect(valueFor(bottom, edited, fields)).toBe(0.04)
  })
})
