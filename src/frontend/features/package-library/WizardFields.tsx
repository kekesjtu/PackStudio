import {
  Alert,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
} from '@mui/material'

import type {
  Material,
  TemplateRequest,
  WizardField,
  WizardStep,
  WizardValue,
} from './types'

interface WizardFieldsProps {
  step: WizardStep
  allFields: WizardField[]
  request: TemplateRequest
  materials: Material[]
  onChange: (request: TemplateRequest) => void
}

export default function WizardFields({
  step,
  allFields,
  request,
  materials,
  onChange,
}: WizardFieldsProps) {
  const labelValues = fieldValues(allFields, request)
  const update = (field: WizardField, value: WizardValue) => {
    if (field.control === 'material' && field.material_group_id) {
      const material_assignments = { ...request.material_assignments }
      if (sameValue(value, field.default)) delete material_assignments[field.material_group_id]
      else material_assignments[field.material_group_id] = String(value)
      onChange({ ...request, material_assignments })
      return
    }
    const overrides = { ...request.overrides }
    if (sameValue(value, field.default)) delete overrides[field.target_id]
    else overrides[field.target_id] = value
    onChange(pruneInactiveMaterials({ ...request, overrides }, allFields))
  }

  return (
    <Stack spacing={2}>
      {step.fields.some((field) => field.minimum !== null && field.minimum !== undefined) && (
        <Alert severity="info" icon={false}>
          “允许范围”是模板的输入边界，超出时无法生成模型；它不代表仿真结果或精度已经过该区间验证。
        </Alert>
      )}
      {step.fields.map((field) => {
        if (!isVisible(field, labelValues)) return null
        const enabled = field.editable && matches(field.enabled_when, labelValues)
        return (
          <Field
            key={field.target_id}
            field={field}
            value={valueFor(field, request)}
            enabled={enabled}
            materials={materials}
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
  materials,
  onChange,
}: {
  field: WizardField
  value: WizardValue
  enabled: boolean
  materials: Material[]
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
  if (field.control === 'material') {
    return (
      <TextField
        select
        label={field.label}
        value={value ?? ''}
        disabled={!enabled}
        size="small"
        helperText={`此组件仅开放 ${field.options.length} 种模板允许材料`}
        slotProps={{ select: { native: true } }}
        onChange={(event) => onChange(event.target.value)}
      >
        {field.options.map((option) => (
          <option key={String(option)} value={String(option)}>
            {materialName(String(option), materials)}
          </option>
        ))}
      </TextField>
    )
  }
  const numeric = ['number', 'integer', 'integer_spinbox'].includes(field.control)
  const values = field.supported_values.filter((item) => item !== null)
  const useSelect = !numeric && values.length > 1
  const numericValues = [field.minimum, field.maximum].filter(
    (item): item is number => typeof item === 'number',
  )
  const interval =
    numericValues.length === 2
      ? `允许范围 ${numericValues[0]} – ${numericValues[1]}${field.unit ? ` ${field.unit}` : ''}`
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
  field.control === 'material' && field.material_group_id
    ? request.material_assignments[field.material_group_id] ?? field.default
    : request.overrides[field.target_id] ?? field.default

function fieldValues(fields: WizardField[], request: TemplateRequest) {
  const values = new Map<string, WizardValue>()
  for (const field of fields) {
    const value = valueFor(field, request)
    values.set(field.label, value)
    if (field.property_name) values.set(field.property_name, value)
  }
  return values
}

function pruneInactiveMaterials(
  request: TemplateRequest,
  fields: WizardField[],
): TemplateRequest {
  const values = fieldValues(fields, request)
  const activeGroups = new Set(
    fields
      .filter(
        (field) =>
          field.control === 'material' &&
          field.material_group_id &&
          isVisible(field, values),
      )
      .map((field) => field.material_group_id as string),
  )
  return {
    ...request,
    material_assignments: Object.fromEntries(
      Object.entries(request.material_assignments).filter(([groupId]) =>
        activeGroups.has(groupId),
      ),
    ),
  }
}

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

const materialName = (identifier: string, materials: Material[]) =>
  materials.find((material) => material.id === identifier)?.name ?? identifier
