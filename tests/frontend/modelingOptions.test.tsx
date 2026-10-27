import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ModelingFields from '../../src/frontend/features/package-library/ModelingFields'
import { renderStep } from '../../src/frontend/features/package-library/WorkspaceSteps'
import type { TemplateRequest, TemplateSchema, WizardField } from '../../src/frontend/features/package-library/types'
import { request as baseRequest } from './materialQualityFixtures'

function request(template_id: string): TemplateRequest {
  return { ...baseRequest, template_id,
    bga: ['chip_array', 'cbga_fc', 'pbga_fc', 'pbga_wb'].includes(template_id) ? {
      representation: template_id === 'chip_array' ? 'discrete' : 'equivalent',
      center_solder_enabled: false, center_solder_rows: null, center_solder_columns: null,
      solder_removal_enabled: false, removal_rows: null, removal_columns: null, omitted_cells: [],
    } : null,
  }
}

describe('native modeling controls', () => {
  it.each([
    ['chip_array', ['Discrete Cuboids']],
    ['cbga_fc', ['Orthotropic Cuboid', 'Discrete Cuboids']],
    ['pbga_fc', ['Orthotropic Cuboid', 'Discrete Cuboids']],
    ['pbga_wb', ['Isotropic Cuboid', 'Discrete Cuboids', 'Orthotropic Cuboid']],
  ] as const)('matches PACK solder ball choices for %s', (template, options) => {
    const onChange = vi.fn()
    render(<ModelingFields request={request(template)} onChange={onChange} />)
    const select = screen.getByRole('combobox', { name: 'Model Solder Ball Array As' })
    expect(within(select).getAllByRole('option').map((option) => option.textContent)).toEqual(options)
    fireEvent.change(select, { target: { value: template === 'pbga_wb' ? 'isotropic' : 'discrete' } })
    expect(onChange.mock.lastCall?.[0].bga.representation).toBe(template === 'pbga_wb' ? 'isotropic' : 'discrete')
  })

  it.each(['bare_die', 'cbga_fc', 'pbga_fc'])('provides a single enabled bump dropdown for %s', (template) => {
    render(<ModelingFields request={request(template)} onChange={vi.fn()} />)
    const label = template === 'bare_die' ? 'Solder Bump Modeling' : 'Model Flip Chip Bumps As'
    const select = screen.getByRole('combobox', { name: label })
    expect(select).toBeEnabled()
    expect(within(select).getAllByRole('option')).toHaveLength(1)
    expect(select).toHaveDisplayValue('Isotropic Cuboid')
  })

  it.each(['map', 'removal'])('disables both equivalent WB choices for an explicit %s', (mode) => {
    const value = request('pbga_wb')
    value.bga = { ...value.bga!, representation: 'discrete', ball_map_enabled: mode === 'map',
      omitted_cells: mode === 'removal' ? [{ row: 0, column: 0 }] : [] }
    render(<ModelingFields request={value} onChange={vi.fn()} />)
    expect(screen.getByRole('option', { name: 'Isotropic Cuboid' })).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Orthotropic Cuboid' })).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Discrete Cuboids' })).toBeEnabled()
  })

  it.each(['bare_die', 'chip_array', 'cbga_fc', 'pbga_fc', 'pbga_wb', 'pqfp', 'qfn', 'sop'])(
    'places local grid last after all other %s modeling fields', (template) => {
      const runtime = JSON.parse(readFileSync(resolve('runtime_data/templates', `${template}.json`), 'utf8'))
      const fields: WizardField[] = runtime.fields.map((field: { key: string; step: string; options: unknown[] }) => ({
        ...field, target_id: `${template}.${field.key}`, property_name: field.key, ui_location: field.step,
        supported_values: field.options, classification: 'enum_option', evidence_status: 'implemented', editable: true,
      }))
      const schema: TemplateSchema = { template_id: template, schema_version: 'packstudio.wizard/v2',
        steps: [{ id: 'modeling', label: '建模选项', fields: fields.filter((field) => field.ui_location === 'modeling') }],
        has_bga: request(template).bga !== null,
        special_rules: { outline_type: 'standard_outline', die_type: 'actual_type', bga_pattern: null, flip_chip_bumps: null },
      }
      const { container } = render(renderStep(schema, 'packstudio_modeling', fields, request(template), [], vi.fn()))
      const controls = Array.from(container.querySelectorAll('input,select'))
      expect(controls.slice(-2)).toEqual([
        screen.getByRole('switch', { name: '局部网格' }), screen.getByRole('combobox', { name: '网格密度' }),
      ])
    },
  )
})
