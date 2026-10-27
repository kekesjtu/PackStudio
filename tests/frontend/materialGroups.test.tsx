import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import type { TemplateRequest } from '../../src/frontend/features/package-library/types'
import { request, safe, selection } from './materialQualityFixtures'

const copper = { ...safe, id: 'copper', name: 'Copper (Pure)', category: 'Metals' }
const gold = { ...safe, id: 'gold', name: 'Gold (Pure)', category: 'Metals' }
const bt = { ...safe, id: 'bt', name: 'BT', category: 'Substrate Dielectrics' }
const materials = [copper, gold, bt]
const field = { ...selection, default: 'copper', options: ['copper', 'gold', 'bt'] }
const step = { id: 'adhesive', label: '胶', fields: [field] }

describe('material group and member selection', () => {
  it('defaults to the material category and lists only members of the selected group', () => {
    render(<WizardFields step={step} allFields={[field]} request={request}
      materials={materials} onChange={vi.fn()} />)
    expect(screen.getByRole('combobox', { name: '芯片胶材料组' })).toHaveTextContent('Metals')
    fireEvent.mouseDown(screen.getByRole('combobox', { name: '芯片胶材料' }))
    expect(screen.getByRole('option', { name: 'Copper (Pure)' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Gold (Pure)' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'BT' })).not.toBeInTheDocument()
  })

  it('selects a concrete group member and updates the request when switching groups', () => {
    const onChange = vi.fn()
    const view = (value: TemplateRequest) => <WizardFields step={step} allFields={[field]}
      request={value} materials={materials} onChange={onChange} />
    const { rerender } = render(view(request))
    fireEvent.mouseDown(screen.getByRole('combobox', { name: '芯片胶材料组' }))
    fireEvent.click(screen.getByRole('option', { name: 'Substrate Dielectrics' }))
    const changed = onChange.mock.calls[0][0] as TemplateRequest
    expect(changed.material_assignments).toEqual({ 'group-adhesive': 'bt' })
    rerender(view(changed))
    expect(screen.getByRole('combobox', { name: '芯片胶材料' })).toHaveTextContent('BT')
    fireEvent.mouseDown(screen.getByRole('combobox', { name: '芯片胶材料组' }))
    fireEvent.click(screen.getByRole('option', { name: 'Metals' }))
    const restored = onChange.mock.calls[1][0] as TemplateRequest
    expect(restored.material_assignments).toEqual({})
    rerender(view(restored))
    expect(screen.getByRole('combobox', { name: '芯片胶材料' })).toHaveTextContent('Copper (Pure)')
  })

  it('follows a new preset material rather than retaining the previous category', () => {
    const footprint = { ...field, control: 'footprint', material_group_id: null,
      target_id: 'sample.footprint', default: 'A', property_name: 'footprint',
      preset_values: { A: {}, B: {} }, preset_materials: {
        A: { 'group-adhesive': 'copper' }, B: { 'group-adhesive': 'bt' },
      } }
    const allFields = [footprint, field]
    const view = (value: TemplateRequest) => <WizardFields step={step} allFields={allFields}
      request={value} materials={materials} onChange={vi.fn()} />
    const { rerender } = render(view(request))
    rerender(view({ ...request, overrides: { 'sample.footprint': 'B' } }))
    expect(screen.getByRole('combobox', { name: '芯片胶材料组' })).toHaveTextContent('Substrate Dielectrics')
    expect(screen.getByRole('combobox', { name: '芯片胶材料' })).toHaveTextContent('BT')
  })
})
