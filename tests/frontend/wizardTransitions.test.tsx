import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import { restoreTemplateRequest, saveTemplateRequest } from '../../src/frontend/features/package-library/requestStorage'
import updateWizardRequest from '../../src/frontend/features/package-library/updateWizardRequest'
import { valueFor } from '../../src/frontend/features/package-library/wizardValues'
import type { TemplateRequest, TemplateSchema, WizardField } from '../../src/frontend/features/package-library/types'
import fixtures from './fixtures/flipChipSchema.json'

// Generated from the backend schema; each family retains its default and 100-ball footprint.
for (const [templateId, fixture] of Object.entries(fixtures)) {
  const fields = fixture.fields as WizardField[]
  const defaults = fixture.request as TemplateRequest
  const field = (key: string) => fields.find((item) => item.property_name === key)!
  const cover = field('cover.type')
  const footprint = field('footprint.size')
  const lidLength = field('lid.length')

  describe(`${templateId} wizard transitions with real schema`, () => {
    it('selects layer constituents and preserves choices through footprint and storage changes', () => {
      const selections = ['group-bump-solder', 'group-underfill', 'group-bga-solder'].map((group) =>
        fields.find((item) => item.material_group_id === group)!)
      const onChange = vi.fn()
      let request = defaults
      const step = { id: 'materials', label: 'materials', fields: selections }
      const { rerender } = render(<WizardFields step={step} allFields={fields}
        request={request} materials={[]} onChange={onChange} />)
      for (const selection of selections) {
        const choice = selection.options.find((option) => option !== selection.default)!
        fireEvent.mouseDown(screen.getByRole('combobox', { name: selection.label }))
        fireEvent.click(screen.getByRole('option', { name: String(choice) }))
        request = onChange.mock.calls.at(-1)![0] as TemplateRequest
        expect(request.material_assignments[selection.material_group_id!]).toBe(choice)
        rerender(<WizardFields step={step} allFields={fields}
          request={request} materials={[]} onChange={onChange} />)
      }
      const next = updateWizardRequest(request, footprint,
        footprint.options.find((option) => option !== footprint.default)!, fields)
      expect(next.material_assignments).toEqual(request.material_assignments)
      saveTemplateRequest(templateId, next)
      const schema: TemplateSchema = {
        schema_version: 'packstudio.wizard/v2', template_id: templateId,
        steps: [{ id: 'all', label: 'all', fields }], has_bga: true,
        special_rules: { outline_type: 'standard_outline', die_type: 'actual_type',
          bga_pattern: null, flip_chip_bumps: 'thick_orthotropic_equivalent' },
      }
      const restored = restoreTemplateRequest(templateId, defaults, schema)!
      expect(restored.material_assignments).toEqual(request.material_assignments)
      localStorage.removeItem(`packstudio.library.v3.${templateId}`)
    })

    it('preserves cover, power, material and representation while replacing preset dimensions', () => {
      const initial: TemplateRequest = {
        ...defaults, die_power_w: 3,
        bga: { ...defaults.bga!, representation: 'discrete' },
        overrides: {
          [cover.target_id]: 'lid', [lidLength.target_id]: 6.1,
          [field('die.length').target_id]: 1.9, [field('die.power').target_id]: 2,
        },
        material_assignments: { 'group-lid': 'aluminum' },
      }
      const onChange = vi.fn()
      render(<WizardFields step={{ id: 'setup', label: 'setup', fields: [footprint] }}
        allFields={fields} request={initial} materials={[]} onChange={onChange} />)
      const selected = footprint.supported_values.find((value) => value !== footprint.default)!
      fireEvent.change(screen.getByLabelText(footprint.label), { target: { value: selected } })
      const next = onChange.mock.calls[0][0] as TemplateRequest
      expect(valueFor(cover, next, fields)).toBe('lid')
      expect(valueFor(lidLength, next, fields)).toBe(9)
      expect(valueFor(field('die.length'), next, fields)).toBe(2.7)
      expect(valueFor(field('die.power'), next, fields)).toBe(2)
      expect(next.bga?.representation).toBe('discrete')
      expect(next.die_power_w).toBe(3)
      expect(next.material_assignments).toEqual(initial.material_assignments)
      expect(initial.overrides[lidLength.target_id]).toBe(6.1)
    })

    it('drops hidden lid dimensions and materials when switching to plate, then returns to defaults', () => {
      const initial: TemplateRequest = {
        ...defaults, overrides: { [cover.target_id]: 'lid', [lidLength.target_id]: 6.1 },
        material_assignments: { 'group-lid': 'aluminum' },
      }
      const onChange = vi.fn()
      const step = { id: 'cover', label: 'cover', fields: [cover, lidLength] }
      const { rerender } = render(<WizardFields step={step} allFields={fields}
        request={initial} materials={[]} onChange={onChange} />)
      fireEvent.change(screen.getByLabelText(cover.label), { target: { value: 'plate' } })
      const plate = onChange.mock.calls[0][0] as TemplateRequest
      expect(plate.overrides[lidLength.target_id]).toBeUndefined()
      expect(plate.material_assignments['group-lid']).toBeUndefined()
      rerender(<WizardFields step={step} allFields={fields}
        request={plate} materials={[]} onChange={onChange} />)
      expect(screen.queryByLabelText(lidLength.label)).not.toBeInTheDocument()
      fireEvent.change(screen.getByLabelText(cover.label), { target: { value: 'lid' } })
      const returned = onChange.mock.calls[1][0] as TemplateRequest
      expect(valueFor(lidLength, returned, fields)).toBe(6)
      expect(returned.overrides[lidLength.target_id]).toBeUndefined()
    })

    it('cleans previously saved hidden overrides before initial generation', () => {
      const saved: TemplateRequest = {
        ...defaults, overrides: { [cover.target_id]: 'plate', [lidLength.target_id]: 6.1 },
        material_assignments: { 'group-lid': 'aluminum' },
      }
      saveTemplateRequest(templateId, saved)
      const schema: TemplateSchema = {
        schema_version: 'packstudio.wizard/v2', template_id: templateId,
        steps: [{ id: 'all', label: 'all', fields }], has_bga: true,
        special_rules: { outline_type: 'standard_outline', die_type: 'actual_type',
          bga_pattern: null, flip_chip_bumps: null },
      }
      const restored = restoreTemplateRequest(templateId, defaults, schema)!
      expect(valueFor(cover, restored, fields)).toBe('plate')
      expect(restored.overrides[lidLength.target_id]).toBeUndefined()
      expect(restored.material_assignments['group-lid']).toBeUndefined()
      localStorage.removeItem(`packstudio.library.v3.${templateId}`)
    })

    it('cleans overrides of disabled fields as well as hidden fields', () => {
      const enabledLength = { ...lidLength, visible_when: undefined,
        enabled_when: { 'cover.type': 'lid' } }
      const disabledFields = fields.map((item) =>
        item.target_id === lidLength.target_id ? enabledLength : item)
      const initial = { ...defaults,
        overrides: { [cover.target_id]: 'lid', [lidLength.target_id]: 6.1 } }
      const next = updateWizardRequest(initial, cover, 'plate', disabledFields)
      expect(next.overrides[lidLength.target_id]).toBeUndefined()
    })
  })
}
