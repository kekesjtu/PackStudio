import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import MetalLayerTable from '../../src/frontend/features/package-library/MetalLayerTable'
import SopNominalPaths from '../../src/frontend/features/package-library/SopNominalPaths'
import updateWizardRequest from '../../src/frontend/features/package-library/updateWizardRequest'
import type { TemplateRequest, WizardField } from '../../src/frontend/features/package-library/types'

const request: TemplateRequest = { template_id: 'sop', design_name: null, overrides: {},
  bga: null, material_assignments: {}, custom_materials: [], die_power_w: null }

function field(key: string, value: number | string | boolean): WizardField {
  return { target_id: `sop.${key}`, property_name: key, default: value, label: key,
    ui_location: 'bond_wires', component: null, control: 'number', options: [],
    classification: 'numeric_parameter', supported_values: [], evidence_status: 'implemented', editable: true }
}

describe('remaining native modeling controls', () => {
  it('shows read-only SOP paths from the actual flag, attach, die and lead endpoints', () => {
    const fields = Object.entries({ 'die.length': 2, 'die.width': 1.5, 'flag.length': 3,
      'flag.width': 2.5, 'leads.gap': 0.2, 'flag.thickness': 0.25, 'leads.thickness': 0.15,
      'die.thickness': 0.35, 'die.attach': 0.05, 'flag.downset': 0.2 }).map(([k, v]) => field(k, v))
    const view = render(<SopNominalPaths request={request} fields={fields} />)
    expect(screen.getByLabelText('左右名义路径长度')).toHaveValue('1')
    expect(screen.getByLabelText('上下名义路径长度')).toHaveAttribute('readonly')
    view.rerender(<SopNominalPaths request={{ ...request, overrides: { 'sop.die.attach': 0.1 } }} fields={fields} />)
    expect(screen.getByLabelText('左右名义路径长度')).toHaveValue('1.05')
  })

  it('initializes exposed pad contact and thermal land with the native dimensions', () => {
    const exposed = { ...field('package.exposed_pad', false), control: 'checkbox' }
    const fields = [exposed, field('leads.height', 0.6), field('flag.downset', 0.4),
      field('thermal_land.enabled', false), field('thermal_land.thickness', 0.02)]
    const next = updateWizardRequest(request, exposed, true, fields)
    expect(next.overrides).toMatchObject({ 'sop.flag.downset': 0.6,
      'sop.thermal_land.enabled': true, 'sop.thermal_land.thickness': 0.07 })
  })

  it('preserves layer geometry while toggling a WB via disconnect', () => {
    const onChange = vi.fn()
    render(<MetalLayerTable label="金属层表" enabled disconnect onChange={onChange}
      value={JSON.stringify([{ depth: 0.2, thickness: 0.036, coverage: 90, disconnect: false }])} />)
    fireEvent.click(screen.getByLabelText('金属层表 第 1 行 disconnect'))
    expect(JSON.parse(onChange.mock.calls[0][0])).toEqual([
      { depth: 0.2, thickness: 0.036, coverage: 90, disconnect: true },
    ])
  })

  it('applies footprint-specific WB four-layer initialization to the request', () => {
    const footprint = { ...field('footprint.size', 'PBGA_121_15X15mm'),
      target_id: 'pbga_wb.footprint.size', control: 'footprint' }
    const layers: WizardField = { ...field('substrate.layers', '2-Layer'),
      target_id: 'pbga_wb.substrate.layers', layer_initialization: {
        PBGA_121_15X15mm: { '4-Layer': { 'pbga_wb.substrate.thickness': 0.56,
          'pbga_wb.vias.rows': 3, 'pbga_wb.vias.columns': 3,
          'pbga_wb.metal.layers': '[{"depth":0,"thickness":0.018,"coverage":30}]' } },
      } }
    const next = updateWizardRequest({ ...request, template_id: 'pbga_wb' }, layers,
      '4-Layer', [footprint, layers])
    expect(next.overrides).toMatchObject({ 'pbga_wb.substrate.layers': '4-Layer',
      'pbga_wb.substrate.thickness': 0.56, 'pbga_wb.vias.rows': 3, 'pbga_wb.vias.columns': 3 })
  })
})
