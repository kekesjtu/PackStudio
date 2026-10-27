import Alert from '@mui/material/Alert'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import FieldShell from '../../ui/FieldShell'
import numericInput from '../../ui/numericInput'
import MaterialSelect from './MaterialSelect'
import MetalLayerTable from './MetalLayerTable'

import { defaultFor, fieldValues, filterFootprints, isVisible, matches, valueFor } from './wizardValues'
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
  const available = new Map([...materials, ...request.custom_materials].map((item) => [item.id, item]))
  const update = (field: WizardField, value: WizardValue) => {
    onChange(updateWizardRequest(request, field, value, allFields))
  }

  return (
    <Stack spacing={1.5}>
      {step.fields.map((field) => {
        if (!isVisible(field, labelValues)) return null
        const enabled = field.editable && matches(field.enabled_when, labelValues)
        return (
          <Field
            key={field.target_id}
            field={field.control === 'material'
              ? { ...field, default: defaultFor(field, request, allFields) }
              : filterFootprints(field, allFields, request)}
            value={valueFor(field, request, allFields)}
            enabled={enabled}
            materials={[...available.values()]}
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
  if (field.control === 'table') return <MetalLayerTable label={field.label}
    value={String(value ?? '[]')} enabled={enabled} onChange={onChange}
    outerFaces={['chip_array.metal.layers', 'pbga_wb.metal.layers'].includes(field.target_id)}
    disconnect={field.target_id === 'pbga_wb.metal.layers'} />
  if (field.control === 'checkbox') {
    return (
      <Stack spacing={0.5}>
        <FormControlLabel
          className="field-switch"
          control={
            <Switch
              checked={Boolean(value)}
              disabled={!enabled}
              onChange={(event) => onChange(event.target.checked)}
            />
          }
          label={field.label}
        />
        {field.help_text && <Typography variant="caption" color="text.secondary">{field.help_text}</Typography>}
      </Stack>
    )
  }
  if (field.control === 'material') {
    return (
      <MaterialSelect field={field} value={value} enabled={enabled} materials={materials} onChange={onChange} />
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
    <FieldShell label={field.label} hint={field.help_text ?? interval} disabled={!enabled}>
      <TextField
        value={value ?? ''}
        type={numeric && !useSelect ? 'number' : undefined}
        select={useSelect}
        disabled={!enabled}
        size="small"
        slotProps={
          useSelect
            ? { select: { native: true, inputProps: { 'aria-label': field.label } } }
            : {
                htmlInput: {
                  'aria-label': field.label,
                  ...(numeric ? numericInput(field.control.startsWith('integer')) : {}),
                  ...(numericValues.length > 1
                    ? { min: Math.min(...numericValues), max: Math.max(...numericValues) }
                    : {}),
                },
              }
        }
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
    </FieldShell>
  )
}
