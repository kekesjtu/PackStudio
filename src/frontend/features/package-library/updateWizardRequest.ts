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
  if (field.property_name === 'package.exposed_pad' && value === true) {
    const height = fields.find((f) => f.property_name === 'leads.height')!
    overrides[request.template_id + '.flag.downset'] = valueFor(height, request, fields)
    overrides[request.template_id + '.thermal_land.enabled'] = true
    overrides[request.template_id + '.thermal_land.thickness'] = 0.07
  }
  if (field.property_name === 'substrate.layers' && field.layer_initialization) {
    const footprint = fields.find((f) => f.control === 'footprint')!
    const preset = String(valueFor(footprint, request, fields))
    Object.assign(overrides, field.layer_initialization[preset]?.[String(value)])
  }
  if (field.property_name === 'substrate.layers' && request.template_id === 'chip_array') {
    const height = value === '4-Layer' ? 0.56 : 0.36
    const prefix = request.template_id + '.'
    const read = (key: string, fallback: number) => {
      const input = fields.find((f) => f.property_name === key)
      return input ? Number(valueFor(input, request, fields)) : fallback
    }
    const top = read('trace.top_thickness', 0.018), bottom = read('trace.bottom_thickness', 0.018)
    const gap = (height - top - bottom - 2 * 0.036) / 3
    const layers = [
      { depth: 0, thickness: top, coverage: 20 },
      ...(value === '4-Layer' ? [
        { depth: top + gap, thickness: 0.036, coverage: 90 },
        { depth: top + 2 * gap, thickness: 0.036, coverage: 90 },
      ] : []),
      { depth: height - bottom, thickness: bottom, coverage: 10 },
    ]
    overrides[prefix + 'substrate.thickness'] = height
    overrides[prefix + 'metal.layers'] = JSON.stringify(layers)
  }
  if (field.property_name === 'bumps.enabled' && value === true && request.template_id === 'bare_die') {
    overrides['bare_die.die.flipped'] = true
  }
  if (['chip_array', 'pbga_wb'].includes(request.template_id)) {
    const tableField = fields.find((candidate) => candidate.property_name === 'metal.layers')
    const tableValue = field.property_name === 'metal.layers' ? value
      : tableField ? valueFor(tableField, request, fields) : null
    if (tableField && typeof tableValue === 'string') {
      const layers = JSON.parse(tableValue) as Array<{ depth: number; thickness: number | null; coverage: number }>
      if (layers.length >= 2) {
        if (field.property_name === 'metal.layers') {
          overrides[request.template_id + '.trace.top_thickness'] = layers[0].thickness
          overrides[request.template_id + '.trace.bottom_thickness'] = layers.at(-1)!.thickness
        } else if (field.property_name === 'trace.top_thickness' || field.property_name === 'trace.bottom_thickness') {
          layers[field.property_name === 'trace.top_thickness' ? 0 : layers.length - 1].thickness = value as number | null
          overrides[tableField.target_id] = JSON.stringify(layers)
        }
      }
    }
  }
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
  const selected = activeRequest({ ...next, bga }, fields)
  const layers = fields.find((candidate) => candidate.property_name === 'substrate.layers')
  if (layers && ['chip_array', 'pbga_wb'].includes(request.template_id) && valueFor(layers, selected, fields) === '4-Layer') {
    return updateWizardRequest(selected, layers, '4-Layer', fields)
  }
  const exposed = fields.find((candidate) => candidate.property_name === 'package.exposed_pad')
  if (exposed && valueFor(exposed, selected, fields)) {
    return updateWizardRequest(selected, exposed, true, fields)
  }
  return selected
}

function activeRequest(request: TemplateRequest, fields: WizardField[]) {
  return pruneViaConfiguration(pruneInactiveMaterials(pruneInactiveOverrides(request, fields), fields), fields)
}
