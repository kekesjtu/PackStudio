import type { TemplateRequest, TemplateSchema } from './types'

const storageKey = (templateId: string) => `packstudio.library.v2.${templateId}`

export function saveTemplateRequest(
  templateId: string,
  request: TemplateRequest,
) {
  localStorage.setItem(storageKey(templateId), JSON.stringify(request))
}

export function restoreTemplateRequest(
  templateId: string,
  defaults: TemplateRequest,
  schema: TemplateSchema,
): TemplateRequest | null {
  try {
    const serialized = localStorage.getItem(storageKey(templateId))
    if (!serialized) return null
    const stored = JSON.parse(serialized) as TemplateRequest
    if (stored.template_id !== templateId) return null
    const fields = schema.steps.flatMap((step) => step.fields)
    const targetIds = new Set(fields.map((field) => field.target_id))
    const materialOptions = new Map(
      fields
        .filter((field) => field.control === 'material' && field.material_group_id)
        .map((field) => [
          field.material_group_id as string,
          new Set(field.options.map(String)),
        ]),
    )
    return {
      ...defaults,
      ...stored,
      overrides: Object.fromEntries(
        Object.entries(stored.overrides ?? {}).filter(([targetId]) =>
          targetIds.has(targetId),
        ),
      ),
      material_assignments: Object.fromEntries(
        Object.entries(stored.material_assignments ?? {}).filter(
          ([groupId, materialId]) => materialOptions.get(groupId)?.has(materialId),
        ),
      ),
      custom_materials: stored.custom_materials ?? [],
      mesh: { ...defaults.mesh, ...stored.mesh },
      environment: { ...defaults.environment, ...stored.environment },
    }
  } catch {
    return null
  }
}
