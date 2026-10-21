import type { TemplateRequest, WizardField, WizardValue } from './types'
import { defaultFor, pruneInactiveOverrides, pruneInactiveMaterials, sameValue, valueFor } from './wizardValues'
import { pruneViaConfiguration } from './viaConfiguration'

export default function updateWizardRequest(
  request: TemplateRequest,
  field: WizardField,
  value: WizardValue,
  fields: WizardField[],
): TemplateRequest {
  if (field.control === 'material' && field.material_group_id) {
    const material_assignments = { ...request.material_assignments }
    if (sameValue(value, defaultFor(field, request, fields))) {
      delete material_assignments[field.material_group_id]
    } else material_assignments[field.material_group_id] = String(value)
    return { ...request, material_assignments }
  }
  if (field.property_name === 'package.type') {
    const footprint = fields.find((item) => item.control === 'footprint')
    const matching = Object.entries(footprint?.preset_values ?? {}).find(([, preset]) =>
      preset[field.target_id] === value,
    )
    if (!footprint || !matching) return request
    return selectFootprint(request, footprint, matching[0], fields)
  }
  if (field.control === 'footprint') return selectFootprint(request, field, value, fields)
  const overrides = { ...request.overrides }
  if (sameValue(value, defaultFor(field, request, fields))) delete overrides[field.target_id]
  else overrides[field.target_id] = value
  return activeRequest({ ...request, overrides }, fields)
}

function selectFootprint(
  request: TemplateRequest,
  footprint: WizardField,
  value: WizardValue,
  fields: WizardField[],
): TemplateRequest {
  const overrides = { ...request.overrides, [footprint.target_id]: value }
  const linked = new Set(Object.values(footprint.preset_values ?? {}).flatMap(Object.keys))
  const independent = fields.filter((field) => linked.has(field.target_id) && (
    field.control === 'checkbox' || field.property_name === 'die.power' ||
    (field.options.length > 1 && field.property_name !== 'package.type')
  ))
  const preserved = independent.map((field) => [field, valueFor(field, request, fields)] as const)
  for (const targetId of linked) delete overrides[targetId]
  const next = { ...request, overrides }
  for (const [field, previous] of preserved) {
    if (!sameValue(previous, defaultFor(field, next, fields))) overrides[field.target_id] = previous
  }
  const pattern = footprint.preset_bga?.[String(value)]
  const bga = pattern && request.bga
    ? { ...pattern, representation: request.bga.representation } : request.bga
  return activeRequest({ ...next, bga }, fields)
}

function activeRequest(request: TemplateRequest, fields: WizardField[]) {
  return pruneViaConfiguration(pruneInactiveMaterials(pruneInactiveOverrides(request, fields), fields), fields)
}
