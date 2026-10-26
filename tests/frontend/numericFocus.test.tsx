import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import NumberInput from '../../src/frontend/features/model-editor/NumberInput'
import WizardFields from '../../src/frontend/features/package-library/WizardFields'
import type {
  TemplateRequest,
  WizardField,
} from '../../src/frontend/features/package-library/types'

const request: TemplateRequest = {
  template_id: 'sample',
  design_name: '示例',
  overrides: {},
  bga: null,
  material_assignments: {},
  custom_materials: [],
  die_power_w: null,
}

const numericField: WizardField = {
  target_id: 'sample.die.length',
  ui_location: 'die',
  component: 'die',
  label: '芯片长度',
  control: 'number',
  default: 1.8,
  options: [],
  supported_values: [],
  classification: 'numeric_parameter',
  property_name: 'die.length',
  evidence_status: 'implemented',
  editable: true,
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('numeric input focus selection', () => {
  it('selects the existing value when a number input receives focus', () => {
    const select = vi.spyOn(HTMLInputElement.prototype, 'select')
    render(<NumberInput label="芯片长度" value={1.8} onChange={vi.fn()} />)

    fireEvent.focus(screen.getByLabelText('芯片长度'))

    expect(select).toHaveBeenCalled()
  })

  it('selects the existing value for numeric wizard fields', () => {
    const select = vi.spyOn(HTMLInputElement.prototype, 'select')
    render(
      <WizardFields
        step={{ id: 'die', label: '芯片', fields: [numericField] }}
        allFields={[numericField]}
        request={request}
        materials={[]}
        onChange={vi.fn()}
      />,
    )

    fireEvent.focus(screen.getByLabelText('芯片长度'))

    expect(select).toHaveBeenCalled()
  })
})
