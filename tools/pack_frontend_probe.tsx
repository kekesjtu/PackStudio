// Research harness copied to tests/frontend by audit_pack_frontend.py.
import { readFileSync, writeFileSync } from 'node:fs'
import { fireEvent, render, screen, cleanup } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import { valueFor } from '../../src/frontend/features/package-library/wizardValues'
import type { TemplateRequest, WizardField } from '../../src/frontend/features/package-library/types'

const schemas = JSON.parse(readFileSync(process.env.PACK_AUDIT_SCHEMA!, 'utf8')) as
  Record<string, { fields: WizardField[]; request: TemplateRequest }>
const findings: object[] = []

describe('real schema interaction audit', () => {
  for (const [templateId, { fields, request }] of Object.entries(schemas)) {
    it(`${templateId} observes footprint and hidden branch transitions`, () => {
      const footprint = fields.find((f) => f.control === 'footprint')!
      const cover = fields.find((f) => f.property_name === 'cover.type')!
      const length = fields.find((f) => f.property_name === 'lid.length')!
      const onChange = vi.fn()
      const initial = { ...request, overrides: { [cover.target_id]: 'lid' } }
      render(<WizardFields step={{ id: 'probe', label: 'probe', fields: [footprint] }}
        allFields={fields} request={initial} materials={[]} onChange={onChange} />)
      const selected = footprint.supported_values.find((p) => p !== footprint.default)!
      fireEvent.change(screen.getByLabelText(footprint.label), { target: { value: selected } })
      expect(onChange).toHaveBeenCalledOnce()
      const afterFootprint = onChange.mock.calls[0][0] as TemplateRequest
      findings.push({ template_id: templateId, scenario: 'footprint_preserves_cover',
        before: 'lid', after: valueFor(cover, afterFootprint, fields), request: afterFootprint })
      cleanup()
      onChange.mockClear()
      const edited = { ...initial, overrides: {
        ...initial.overrides, [length.target_id]: Number(valueFor(length, initial, fields)) + 0.1,
      } }
      render(<WizardFields step={{ id: 'probe', label: 'probe', fields: [cover] }}
        allFields={fields} request={edited} materials={[]} onChange={onChange} />)
      fireEvent.change(screen.getByLabelText(cover.label), { target: { value: 'plate' } })
      expect(onChange).toHaveBeenCalledOnce()
      findings.push({ template_id: templateId, scenario: 'cover_prunes_hidden_overrides',
        hidden_target: length.target_id, request: onChange.mock.calls[0][0] })
      cleanup()
    })
  }
  it('saves observed requests for independent backend validation', () => {
    expect(findings).toHaveLength(4)
    writeFileSync(process.env.PACK_AUDIT_FRONTEND_OUTPUT!, JSON.stringify(findings, null, 2))
  })
})
