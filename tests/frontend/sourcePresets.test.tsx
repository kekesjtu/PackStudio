import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import BgaConfigurationPanel from '../../src/frontend/features/package-library/BgaConfigurationPanel'
import type {
  BgaConfiguration, TemplateRequest, WizardField,
} from '../../src/frontend/features/package-library/types'

const basePattern: BgaConfiguration = {
  representation: 'equivalent', center_solder_enabled: false,
  center_solder_rows: 1, center_solder_columns: 1, solder_removal_enabled: false,
  removal_rows: 3, removal_columns: 3, omitted_cells: [], allow_asymmetric_regions: false,
}
const sourcePattern: BgaConfiguration = {
  ...basePattern, solder_removal_enabled: true, removal_rows: 0, removal_columns: 0,
  omitted_cells: [{ row: 0, column: 0 }],
}
const footprint: WizardField = {
  target_id: 'sample.footprint.size', ui_location: 'package_setup', component: 'package_setup',
  label: '源规格', control: 'footprint', default: 'baseline', options: ['baseline', 'source'],
  classification: 'jedec_preset', property_name: 'footprint.size',
  supported_values: ['baseline', 'source'], evidence_status: 'implemented', editable: true,
  preset_values: { baseline: { 'sample.die.length': 1 }, source: { 'sample.die.length': 2 } },
  preset_bga: { baseline: basePattern, source: sourcePattern },
  preset_notes: { source: '源坐标列表包含缺球' },
}
const request: TemplateRequest = {
  template_id: 'sample', design_name: 'sample',
  overrides: { 'sample.die.length': 1.5, 'sample.cover.type': 'lid_cap' },
  bga: { ...basePattern, representation: 'discrete' }, material_assignments: {},
  custom_materials: [], die_power_w: 2, mesh: { resolution: 'standard' },
}

describe('source presets', () => {
  it('applies the source pattern while preserving representation and independent choices', () => {
    const onChange = vi.fn()
    const { rerender } = render(<WizardFields step={{ id: 'package_setup', label: '规格', fields: [footprint] }}
      allFields={[footprint]} request={request} materials={[]} onChange={onChange} />)
    fireEvent.change(screen.getByLabelText('源规格'), { target: { value: 'source' } })
    const next = onChange.mock.calls[0][0] as TemplateRequest
    expect(next.bga).toEqual({ ...sourcePattern, representation: 'discrete' })
    expect(next.overrides).toEqual({ 'sample.footprint.size': 'source', 'sample.cover.type': 'lid_cap' })
    expect(next.die_power_w).toBe(2)
    rerender(<WizardFields step={{ id: 'package_setup', label: '规格', fields: [footprint] }}
      allFields={[footprint]} request={next} materials={[]} onChange={onChange} />)
    expect(screen.getByText('源坐标列表包含缺球')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('源规格'), { target: { value: 'baseline' } })
    expect(onChange.mock.calls[1][0].bga).toEqual({ ...basePattern, representation: 'discrete' })
  })

  it('clears explicit omissions when removal is switched off', () => {
    const onChange = vi.fn()
    render(<BgaConfigurationPanel value={sourcePattern} section="removal" onChange={onChange} />)
    fireEvent.click(screen.getByLabelText('焊球去除'))
    expect(onChange.mock.calls[0][0].solder_removal_enabled).toBe(false)
    expect(onChange.mock.calls[0][0].omitted_cells).toEqual([])
  })

  it('filters native subtypes and updates dimensions and materials together', () => {
    const subtype: WizardField = {
      ...footprint, target_id: 'sample.package.type', property_name: 'package.type',
      control: 'combobox', label: 'Package Type', default: 'lqfp',
      options: ['lqfp', 'mqfp'], supported_values: ['lqfp', 'mqfp'],
      preset_values: undefined, preset_bga: undefined, preset_notes: undefined,
    }
    const typedFootprint: WizardField = {
      ...footprint,
      preset_values: {
        baseline: { 'sample.package.type': 'lqfp', 'sample.die.length': 1 },
        source: { 'sample.package.type': 'mqfp', 'sample.die.length': 2 },
      },
      preset_materials: {
        baseline: { 'group-die': 'copper' }, source: { 'group-die': 'gold' },
      },
    }
    const die: WizardField = {
      ...subtype, target_id: 'sample.die.length', property_name: 'die.length',
      label: '芯片长度', control: 'number', default: 1, options: [], supported_values: [],
    }
    const material: WizardField = {
      ...subtype, target_id: 'sample.material.die', property_name: 'material.group-die',
      material_group_id: 'group-die', label: '芯片材料', control: 'material',
      default: 'copper', options: ['copper', 'gold'], supported_values: ['copper', 'gold'],
    }
    const fields = [subtype, typedFootprint, die, material]
    const onChange = vi.fn()
    const { rerender } = render(<WizardFields step={{ id: 'package_setup', label: '规格', fields }}
      allFields={fields} request={request} materials={[]} onChange={onChange} />)
    expect(screen.getByLabelText('源规格').querySelectorAll('option')).toHaveLength(1)
    fireEvent.change(screen.getByLabelText('Package Type'), { target: { value: 'mqfp' } })
    const next = onChange.mock.calls[0][0] as TemplateRequest
    expect(next.overrides).toEqual({ 'sample.footprint.size': 'source', 'sample.cover.type': 'lid_cap' })
    expect(next.bga?.representation).toBe('discrete')
    rerender(<WizardFields step={{ id: 'package_setup', label: '规格', fields }}
      allFields={fields} request={next} materials={[]} onChange={onChange} />)
    expect(screen.getByLabelText('Package Type')).toHaveValue('mqfp')
    expect(screen.getByLabelText('源规格')).toHaveValue('source')
    expect(screen.getByLabelText('芯片长度')).toHaveValue(2)
    expect(screen.getByRole('combobox', { name: '芯片材料' })).toHaveTextContent('gold')
    expect(next.material_assignments).toEqual({})
  })
})
