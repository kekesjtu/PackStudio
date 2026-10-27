import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WorkspaceNavigation from '../../src/frontend/features/package-library/WorkspaceNavigation'
import { renderStep } from '../../src/frontend/features/package-library/WorkspaceSteps'
import type { TemplateRequest, TemplateSchema, WizardField } from '../../src/frontend/features/package-library/types'
import fixtures from './fixtures/flipChipSchema.json'

const fields = fixtures.cbga_fc.fields as WizardField[]
const request = fixtures.cbga_fc.request as TemplateRequest
const schema: TemplateSchema = {
  template_id: 'cbga_fc', schema_version: 'packstudio.wizard/v2', has_bga: true,
  steps: ['slug', 'modeling'].map((id) => ({ id, label: id, fields: fields.filter((f) => f.ui_location === id) })),
  special_rules: { outline_type: 'standard_outline', die_type: 'actual_type', bga_pattern: null, flip_chip_bumps: null },
}

describe('modeling and conditional Slug controls', () => {
  it('has one modeling entry containing both BGA representation and local grid controls', () => {
    render(<><WorkspaceNavigation schema={schema} activeStep="packstudio_modeling" onSelect={vi.fn()} />
      {renderStep(schema, 'packstudio_modeling', fields, request, [], vi.fn())}</>)
    expect(screen.getAllByRole('button', { name: '建模选项' })).toHaveLength(1)
    expect(screen.queryByRole('button', { name: 'modeling' })).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'BGA 焊球阵列建模' })).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: '局部网格' })).toBeInTheDocument()
    expect(screen.getByLabelText('网格密度')).toBeInTheDocument()
  })

  it('keeps the CBGA Slug switch visible, disabled and explained until encapsulant is selected', () => {
    const onChange = vi.fn()
    const view = (value: TemplateRequest) => renderStep(schema, 'slug', fields, value, [], onChange)
    const { rerender } = render(view(request))
    expect(screen.getByRole('switch', { name: '包含嵌入式散热块' })).toBeDisabled()
    expect(screen.getByText('顶部结构选择“塑封体（Encapsulant）”时可用。')).toBeInTheDocument()
    rerender(view({ ...request, overrides: { 'cbga_fc.cover.type': 'encapsulant' } }))
    const toggle = screen.getByRole('switch', { name: '包含嵌入式散热块' })
    expect(toggle).toBeEnabled()
    fireEvent.click(toggle)
    expect(onChange.mock.calls[0][0].overrides['cbga_fc.slug.enabled']).toBe(true)
  })

  it('keeps a modeling entry for Bare Die local grid settings', () => {
    render(<WorkspaceNavigation schema={{ ...schema, template_id: 'bare_die', has_bga: false,
      steps: schema.steps.filter((s) => s.id === 'modeling') }} activeStep="packstudio_modeling" onSelect={vi.fn()} />)
    expect(screen.getByRole('button', { name: '建模选项' })).toBeInTheDocument()
  })
})
