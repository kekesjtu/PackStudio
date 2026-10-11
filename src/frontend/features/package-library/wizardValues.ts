import type { TemplateRequest, WizardField, WizardValue } from './types'

export function valueFor(
  field: WizardField,
  request: TemplateRequest,
  allFields: WizardField[],
) {
  if (field.control === 'material' && field.material_group_id) {
    return request.material_assignments[field.material_group_id] ??
      defaultFor(field, request, allFields)
  }
  if (request.overrides[field.target_id] !== undefined) {
    return request.overrides[field.target_id]
  }
  return defaultFor(field, request, allFields)
}

export function defaultFor(
  field: WizardField,
  request: TemplateRequest,
  allFields: WizardField[],
) {
  for (const controller of allFields) {
    if (!controller.preset_values) continue
    const selected = request.overrides[controller.target_id] ?? controller.default
    if (field.material_group_id) {
      const material = controller.preset_materials?.[String(selected)]?.[field.material_group_id]
      if (material !== undefined) return material
    }
    const presetValue = controller.preset_values[String(selected)]?.[field.target_id]
    if (presetValue !== undefined) return presetValue
  }
  return field.default
}

export function fieldValues(fields: WizardField[], request: TemplateRequest) {
  const values = new Map<string, WizardValue>()
  for (const field of fields) {
    const value = valueFor(field, request, fields)
    values.set(field.label, value)
    if (field.property_name) values.set(field.property_name, value)
  }
  return values
}

export function pruneInactiveMaterials(
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

export function isVisible(field: WizardField, values: Map<string, WizardValue>) {
  if (!matches(field.visible_when, values)) return false
  if (field.hidden_when && matches(field.hidden_when, values)) return false
  return true
}

export function matches(
  conditions: Record<string, WizardValue> | undefined,
  values: Map<string, WizardValue>,
) {
  if (!conditions) return true
  return Object.entries(conditions).every(([label, expected]) =>
    sameValue(values.get(label), expected),
  )
}

export function sameValue(left: unknown, right: unknown) {
  if (typeof left === 'number' && typeof right === 'number') {
    return Math.abs(left - right) <= 1e-12
  }
  return left === right
}

export function filterFootprints(field: WizardField, fields: WizardField[], request: TemplateRequest) {
  if (field.control !== 'footprint') return field
  const subtype = fields.find((item) => item.property_name === 'package.type')
  if (!subtype) return field
  const selected = valueFor(subtype, request, fields)
  return { ...field, supported_values: field.supported_values.filter((preset) =>
    field.preset_values?.[String(preset)]?.[subtype.target_id] === selected,
  ) }
}
