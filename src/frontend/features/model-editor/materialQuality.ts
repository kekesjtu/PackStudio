import type { Material } from './types'

export interface MaterialQualityIssue {
  material: Material
  properties: string[]
}

export default function materialQuality(material: Material): MaterialQualityIssue | null {
  const properties = [
    ...(material.density === 1 ? ['密度 = 1 kg/m³'] : []),
    ...(material.specific_heat === 1 ? ['比热 = 1 J/(kg·K)'] : []),
  ]
  return properties.length ? { material, properties } : null
}
