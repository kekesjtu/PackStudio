import {
  Alert,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
} from '@mui/material'

import { fieldValues, filterFootprints, isVisible, matches, valueFor } from './wizardValues'
import updateWizardRequest from './updateWizardRequest'

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
    onChange(updateWizardRequest(request, field, value, allFields))
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
            field={filterFootprints(field, allFields, request)}
            value={valueFor(field, request, allFields)}
            enabled={enabled}
            materials={materials}
            onChange={(value) => update(field, value)}
          />
        )
      })}
      {step.fields.map((field) => field.preset_notes?.[String(valueFor(field, request, allFields))])
        .filter(Boolean).map((note) => <Alert key={note} severity="warning">{note}</Alert>)}
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
        label={field.label}
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
        helperText="选择组件材料；材料物性可在右侧材料库中调整"
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
  const useSelect = !numeric && (values.length > 1 || field.control === 'footprint')
  const numericValues = [field.minimum, field.maximum].filter(
    (item): item is number => typeof item === 'number',
  )
  const interval =
    field.control === 'footprint'
      ? '选择标准尺寸后会自动填充关联参数，仍可逐项微调'
      : numericValues.length === 2
      ? `允许范围 ${numericValues[0]} – ${numericValues[1]}${field.unit ? ` ${field.unit}` : ''}`
      : undefined
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
            {field.option_labels?.[String(option)] ?? String(option)}
          </option>
        ))}
    </TextField>
  )
}

const materialName = (identifier: string, materials: Material[]) =>
  materials.find((material) => material.id === identifier)?.name ?? identifier
