import {
  Alert,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
} from '@mui/material'

import type {
  TemplateRequest,
  WizardField,
  WizardStep,
  WizardValue,
} from './types'

interface WizardFieldsProps {
  step: WizardStep
  allFields: WizardField[]
  request: TemplateRequest
  onChange: (request: TemplateRequest) => void
}

export default function WizardFields({
  step,
  allFields,
  request,
  onChange,
}: WizardFieldsProps) {
  const labelValues = new Map<string, WizardValue>()
  for (const field of allFields) {
    const value = valueFor(field, request)
    labelValues.set(field.label, value)
    if (field.property_name) labelValues.set(field.property_name, value)
  }
  const update = (field: WizardField, value: WizardValue) => {
    const overrides = { ...request.overrides }
    if (sameValue(value, field.default)) delete overrides[field.target_id]
    else overrides[field.target_id] = value
    onChange({ ...request, overrides })
  }

  return (
    <Stack spacing={2}>
      {step.fields.map((field) => {
        if (!isVisible(field, labelValues)) return null
        const enabled = field.editable && matches(field.enabled_when, labelValues)
        return (
          <Field
            key={field.target_id}
            field={field}
            value={valueFor(field, request)}
            enabled={enabled}
            onChange={(value) => update(field, value)}
          />
        )
      })}
      {!step.fields.some((field) => field.editable) && (
        <Alert severity="info">
          本页字段保留为参考记录；当前没有可安全重放的模型输入。
        </Alert>
      )}
    </Stack>
  )
}

function Field({
  field,
  value,
  enabled,
  onChange,
}: {
  field: WizardField
  value: WizardValue
  enabled: boolean
  onChange: (value: WizardValue) => void
}) {
  if (field.control === 'checkbox') {
    return (
      <FormControlLabel
        control={
          <Switch
            checked={Boolean(value)}
            disabled={!enabled}
            onChange={(event) => onChange(event.target.checked)}
          />
        }
        label={`${field.label}${evidenceSuffix(field)}`}
      />
    )
  }
  const numeric = ['number', 'integer', 'integer_spinbox'].includes(field.control)
  const values = field.supported_values.filter((item) => item !== null)
  const useSelect = !numeric && values.length > 1
  const numericValues = values.filter((item): item is number => typeof item === 'number')
  const interval =
    numericValues.length > 1
      ? `验证区间 ${Math.min(...numericValues)} – ${Math.max(...numericValues)}`
      : evidenceSuffix(field)
  return (
    <TextField
      label={field.label}
      value={value ?? ''}
      type={numeric && !useSelect ? 'number' : undefined}
      select={useSelect}
      disabled={!enabled}
      size="small"
      helperText={interval}
      slotProps={{
        select: { native: true },
        htmlInput:
          numericValues.length > 1
            ? { min: Math.min(...numericValues), max: Math.max(...numericValues) }
            : undefined,
      }}
      onChange={(event) => {
        if (!numeric) return onChange(event.target.value)
        if (event.target.value === '') return onChange(null)
        const parsed = Number(event.target.value)
        onChange(field.control.startsWith('integer') ? Math.round(parsed) : parsed)
      }}
    >
      {useSelect &&
        values.map((option) => (
          <option key={String(option)} value={String(option)}>
            {String(option)}
          </option>
        ))}
    </TextField>
  )
}

const valueFor = (field: WizardField, request: TemplateRequest) =>
  request.overrides[field.target_id] ?? field.default

function isVisible(field: WizardField, values: Map<string, WizardValue>) {
  if (!matches(field.visible_when, values)) return false
  if (field.hidden_when && matches(field.hidden_when, values)) return false
  return true
}

function matches(
  conditions: Record<string, WizardValue> | undefined,
  values: Map<string, WizardValue>,
) {
  if (!conditions) return true
  return Object.entries(conditions).every(([label, expected]) =>
    sameValue(values.get(label), expected),
  )
}

function sameValue(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') {
    return Math.abs(left - right) <= 1e-12
  }
  return left === right
}

const evidenceSuffix = (field: WizardField) =>
  field.evidence_status === 'implemented' ? ' · 原生实现' : ''
