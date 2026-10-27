import type { Material, WizardField } from './types'

const nativeOrder = [
  'Alloys (Leadframe)', 'Alloys (Other)', 'Alloys (Solders)', 'Attachment Materials',
  'Ceramics', 'Metals', 'Others', 'Resins', 'Semiconductors', 'Substrate Dielectrics',
]

export function groupedMaterials(field: Pick<WizardField, 'options'>, materials: Material[]) {
  const available = new Map(materials.map((material) => [material.id, material]))
  const groups = new Map<string, string[]>()
  for (const option of field.options) {
    if (typeof option !== 'string' || !option) continue
    const category = available.get(option)?.category ?? 'Others'
    const members = groups.get(category) ?? []
    members.push(option)
    groups.set(category, members)
  }
  return new Map([...groups].sort(([left], [right]) => {
    const rank = (name: string) => {
      const index = nativeOrder.indexOf(name)
      return index < 0 ? nativeOrder.length : index
    }
    return rank(left) - rank(right) || left.localeCompare(right)
  }))
}
