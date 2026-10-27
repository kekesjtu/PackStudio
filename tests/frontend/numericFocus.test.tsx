import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import NumberInput from '../../src/frontend/features/model-editor/NumberInput'
import MetalLayerTable from '../../src/frontend/features/package-library/MetalLayerTable'
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

describe('numeric input kinds', () => {
  it('uses decimal rules even when the current value is a whole number', () => {
    const onChange = vi.fn()
    render(<NumberInput label="芯片长度" value={2} onChange={onChange} />)
    const input = screen.getByLabelText('芯片长度') as HTMLInputElement

    expect(input).toHaveAttribute('data-numeric-kind', 'decimal')
    expect(input).toHaveAttribute('step', 'any')
    fireEvent.change(input, { target: { value: '2.35' } })
    expect(onChange).toHaveBeenCalledWith(2.35)
    expect(input.validity.stepMismatch).toBe(false)
  })

  it('keeps integer rules and empty values for array counts', () => {
    const onChange = vi.fn()
    render(<NumberInput label="中央行数" value={3} integer allowEmpty onChange={onChange} />)
    const input = screen.getByLabelText('中央行数')

    expect(input).toHaveAttribute('data-numeric-kind', 'integer')
    expect(input).toHaveAttribute('step', '1')
    fireEvent.change(input, { target: { value: '4' } })
    expect(onChange).toHaveBeenCalledWith(4)
    fireEvent.change(input, { target: { value: '' } })
    expect(onChange).toHaveBeenLastCalledWith(null)
  })

  it.each(['number', 'integer', 'integer_spinbox'])(
    'classifies enabled and disabled wizard %s fields from their definition', (control) => {
      const field = { ...numericField, control }
      const onChange = vi.fn()
      const view = (editable: boolean) => <WizardFields
        step={{ id: 'die', label: '芯片', fields: [{ ...field, editable }] }}
        allFields={[field]} request={request} materials={[]} onChange={onChange}
      />
      const { rerender } = render(view(true))
      const input = screen.getByLabelText('芯片长度') as HTMLInputElement
      const integer = control.startsWith('integer')

      expect(input).toHaveAttribute('data-numeric-kind', integer ? 'integer' : 'decimal')
      expect(input).toHaveAttribute('step', integer ? '1' : 'any')
      fireEvent.change(input, { target: { value: integer ? '3' : '1.85' } })
      expect(onChange.mock.lastCall?.[0].overrides[field.target_id]).toBe(integer ? 3 : 1.85)
      expect(input.validity.stepMismatch).toBe(false)

      rerender(view(false))
      expect(input).toBeDisabled()
      expect(input).toHaveAttribute('data-numeric-kind', integer ? 'integer' : 'decimal')
    },
  )

  it('uses decimal rules for metal layer depth, thickness and coverage', () => {
    const onChange = vi.fn()
    render(<MetalLayerTable label="金属层" enabled onChange={onChange}
      value={JSON.stringify([{ depth: 0.2, thickness: 0.035, coverage: 65.5 }])} />)

    for (const key of ['depth', 'thickness', 'coverage']) {
      const input = screen.getByLabelText(`金属层 第 1 行 ${key}`) as HTMLInputElement
      expect(input).toHaveAttribute('data-numeric-kind', 'decimal')
      expect(input).toHaveAttribute('step', 'any')
      expect(input.validity.stepMismatch).toBe(false)
    }
    fireEvent.change(screen.getByLabelText('金属层 第 1 行 thickness'), { target: { value: '0.018' } })
    expect(JSON.parse(onChange.mock.lastCall?.[0])[0].thickness).toBe(0.018)
  })
})
