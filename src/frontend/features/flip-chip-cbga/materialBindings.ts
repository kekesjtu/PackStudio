import type { FlipChipCbgaParameters, Material } from './types'

export type MaterialSlot =
  | 'substrate'
  | 'die'
  | 'encapsulant'
  | 'flip_chip_element'
  | 'flip_chip_matrix'
  | 'solder_ball_element'
  | 'solder_ball_matrix'
  | 'heat_slug'
  | 'heat_slug_interface'
  | 'lid'
  | 'lid_interface'

export const materialSlotLabels: Record<MaterialSlot, string> = {
  substrate: '封装基底',
  die: '芯片',
  encapsulant: '塑封',
  flip_chip_element: '倒装芯片凸块',
  flip_chip_matrix: 'Underfill',
  solder_ball_element: '焊球',
  solder_ball_matrix: '焊球层基体',
  heat_slug: '插入式散热块',
  heat_slug_interface: '散热块界面层',
  lid: '顶盖',
  lid_interface: '顶盖界面层',
}

export function collectMaterialLibrary(parameters: FlipChipCbgaParameters): Material[] {
  const materials = (Object.keys(materialSlotLabels) as MaterialSlot[]).map((slot) =>
    getMaterialForSlot(parameters, slot),
  )
  return [...new Map(materials.map((material) => [material.id, material])).values()]
}

export function getMaterialForSlot(
  parameters: FlipChipCbgaParameters,
  slot: MaterialSlot,
): Material {
  const materials: Record<MaterialSlot, Material> = {
    substrate: parameters.substrate.material,
    die: parameters.die.material,
    encapsulant: parameters.encapsulant.material,
    flip_chip_element: parameters.flip_chip_bumps.element_material,
    flip_chip_matrix: parameters.flip_chip_bumps.matrix_material,
    solder_ball_element: parameters.solder_balls.element_material,
    solder_ball_matrix: parameters.solder_balls.matrix_material,
    heat_slug: parameters.heat_slug.material,
    heat_slug_interface: parameters.heat_slug.interface_material,
    lid: parameters.lid.material,
    lid_interface: parameters.lid.interface_material,
  }
  return materials[slot]
}

export function assignMaterialToSlot(
  parameters: FlipChipCbgaParameters,
  slot: MaterialSlot,
  material: Material,
): FlipChipCbgaParameters {
  switch (slot) {
    case 'substrate':
      return { ...parameters, substrate: { ...parameters.substrate, material } }
    case 'die':
      return { ...parameters, die: { ...parameters.die, material } }
    case 'encapsulant':
      return { ...parameters, encapsulant: { ...parameters.encapsulant, material } }
    case 'flip_chip_element':
      return {
        ...parameters,
        flip_chip_bumps: { ...parameters.flip_chip_bumps, element_material: material },
      }
    case 'flip_chip_matrix':
      return {
        ...parameters,
        flip_chip_bumps: { ...parameters.flip_chip_bumps, matrix_material: material },
      }
    case 'solder_ball_element':
      return {
        ...parameters,
        solder_balls: { ...parameters.solder_balls, element_material: material },
      }
    case 'solder_ball_matrix':
      return {
        ...parameters,
        solder_balls: { ...parameters.solder_balls, matrix_material: material },
      }
    case 'heat_slug':
      return { ...parameters, heat_slug: { ...parameters.heat_slug, material } }
    case 'heat_slug_interface':
      return {
        ...parameters,
        heat_slug: { ...parameters.heat_slug, interface_material: material },
      }
    case 'lid':
      return { ...parameters, lid: { ...parameters.lid, material } }
    case 'lid_interface':
      return { ...parameters, lid: { ...parameters.lid, interface_material: material } }
  }
}

export function replaceMaterialDefinition(
  parameters: FlipChipCbgaParameters,
  material: Material,
): FlipChipCbgaParameters {
  return (Object.keys(materialSlotLabels) as MaterialSlot[]).reduce(
    (current, slot) =>
      getMaterialForSlot(current, slot).id === material.id
        ? assignMaterialToSlot(current, slot, material)
        : current,
    parameters,
  )
}

export function materialUsageLabels(
  parameters: FlipChipCbgaParameters,
  materialId: string,
): string[] {
  return (Object.keys(materialSlotLabels) as MaterialSlot[])
    .filter((slot) => getMaterialForSlot(parameters, slot).id === materialId)
    .map((slot) => materialSlotLabels[slot])
}
