export interface ConductivityTensor {
  x: number
  y: number
  z: number
}

export interface Material {
  id: string
  name: string
  category?: string
  conductivity: ConductivityTensor
  density: number
  specific_heat: number
  color: string
  source?: string | null
  conductivity_coefficient?: number | null
  conductivity_reference_temperature_c?: number | null
}

export type StructureType =
  | 'substrate'
  | 'die'
  | 'encapsulant'
  | 'flip_chip_bump'
  | 'underfill'
  | 'solder_ball'
  | 'static_air'
  | 'thermal_interface'
  | 'heat_slug'
  | 'lid'
  | 'die_attach'
  | 'lead_frame'
  | 'bond_wire'
  | 'solder_mask'
  | 'trace'
  | 'via'
  | 'exposed_pad'
  | 'solder'
  | 'generic'

export interface AxisAlignedBlock {
  id: string
  name: string
  structure_type: StructureType
  origin: { x: number; y: number; z: number }
  size: { x: number; y: number; z: number }
  material_id: string | null
  parent_group_id: string
  metadata: Record<string, string | number | boolean>
}

export interface ModelGroup {
  id: string
  name: string
  parent_id: string | null
  block_ids: string[]
}

export type BlockFace = 'x_min' | 'x_max' | 'y_min' | 'y_max' | 'z_min' | 'z_max'
export type BoundaryKind = 'temperature' | 'heat_flux' | 'convection' | 'adiabatic'

export interface BoundaryCondition {
  id: string
  name: string
  kind: BoundaryKind
  targets: Array<{ block_id: string; face: BlockFace }>
  temperature_k: number | null
  heat_flux_w_m2: number | null
  convection_coefficient_w_m2k: number | null
  ambient_temperature_k: number | null
}

export interface PackageModel {
  warnings?: string[]
  schema_version: 'packstudio.model/v1'
  template_id: string
  name: string
  length_unit: 'mm'
  coordinate_system: {
    origin: string
    x_axis: string
    y_axis: string
    z_axis: string
  }
  materials: Material[]
  blocks: AxisAlignedBlock[]
  groups: ModelGroup[]
  heat_sources: Array<{ id: string; name: string; block_id: string; power_w: number }>
  boundaries: BoundaryCondition[]
  metadata: Record<string, string | number | boolean>
}
