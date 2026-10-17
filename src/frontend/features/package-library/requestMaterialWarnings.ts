import materialQuality from '../model-editor/materialQuality'
import type { MaterialQualityIssue } from '../model-editor/materialQuality'
import type { Material, PackageModel, TemplateRequest, WizardField } from './types'
import { fieldValues, isVisible, matches, valueFor } from './wizardValues'

// These array builders use fixed constituents without material-selection controls.
const arrayConstituents: Record<string, string[]> = {
  'flip-chip-bumps-equivalent': ['solder-pb90', 'underfill'],
  'solder-ball-equivalent': ['solder-sn63', 'static-air'],
}

export default function requestMaterialWarnings(
  fields: WizardField[], request: TemplateRequest, library: Material[], model: PackageModel | null,
): MaterialQualityIssue[] {
  const available = new Map([...library, ...request.custom_materials].map((item) => [item.id, item]))
  const values = fieldValues(fields, request)
  const selected = fields.filter((field) => field.control === 'material' &&
    isVisible(field, values) && matches(field.enabled_when, values))
    .map((field) => String(valueFor(field, request, fields)))
  const visited = new Set<Material>()
  const issues = new Map<string, MaterialQualityIssue>()
  const visit = (material: Material | undefined) => {
    if (!material || visited.has(material)) return
    visited.add(material)
    const issue = materialQuality(material)
    if (issue) {
      const previous = issues.get(material.id)
      issues.set(material.id, { material, properties:
        [...new Set([...(previous?.properties ?? []), ...issue.properties])] })
    }
    // Retained mixture rules record constituents even when the equivalent rho/cp are not 1.
    for (const match of (material.source ?? '').matchAll(/(?:metal|matrix)=([a-z0-9._-]+)/g)) {
      visit(available.get(match[1]))
    }
    for (const id of arrayConstituents[material.id] ?? []) visit(available.get(id))
  }
  selected.forEach((id) => visit(available.get(id)))
  const hasBumps = ['cbga_fc', 'pbga_fc'].includes(request.template_id) ||
    (request.template_id === 'bare_die' && fields.some((field) =>
      field.property_name === 'bumps.enabled' && valueFor(field, request, fields) === true))
  if (hasBumps) arrayConstituents['flip-chip-bumps-equivalent'].forEach((id) => visit(available.get(id)))
  if (request.bga?.representation === 'equivalent') {
    arrayConstituents['solder-ball-equivalent'].forEach((id) => visit(available.get(id)))
  }
  if (model) {
    const usedIds = new Set(model.blocks.map((block) => block.material_id))
    model.materials.filter((item) => usedIds.has(item.id)).forEach(visit)
  }
  return [...issues.values()]
}
