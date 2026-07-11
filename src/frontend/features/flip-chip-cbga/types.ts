export interface ConductivityTensor {
  x: number
  y: number
  z: number
}

export interface Material {
  id: string
  name: string
  conductivity: ConductivityTensor
  density: number
  specific_heat: number
  color: string
  source?: string | null
}

export interface RectangularPartParameters {
  length: number
  width: number
  thickness: number
  material: Material
}

export interface DieParameters extends RectangularPartParameters {
  power_w: number
}

export type ArrayRepresentation = 'discrete' | 'equivalent'
export type ArrayPattern =
  | 'full'
  | 'staggered'
  | 'center_depopulated'
  | 'center_populated'
  | 'custom'
export type VoidFillMode = 'omit' | 'matrix'

export interface CellIndex {
  row: number
  column: number
}

export interface ArrayLayerParameters {
  rows: number
  columns: number
  pitch_x: number
  pitch_y: number
  diameter: number
  height: number
  representation: ArrayRepresentation
  pattern: ArrayPattern
  center_rows: number
  center_columns: number
  omitted_cells: CellIndex[]
  void_fill: VoidFillMode
  emit_matrix_blocks: boolean
  element_material: Material
  matrix_material: Material
}

export interface HeatSlugParameters extends RectangularPartParameters {
  enabled: boolean
  interface_thickness: number
  interface_material: Material
}

export interface LidParameters extends RectangularPartParameters {
  enabled: boolean
  interface_thickness: number
  interface_material: Material
}

export interface EnvironmentParameters {
  ambient_temperature_k: number
  bottom_convection_coefficient_w_m2k: number | null
  top_convection_coefficient_w_m2k: number | null
}

export interface FlipChipCbgaParameters {
  design_name: string
  substrate: RectangularPartParameters
  die: DieParameters
  flip_chip_bumps: ArrayLayerParameters
  solder_balls: ArrayLayerParameters
  heat_slug: HeatSlugParameters
  lid: LidParameters
  environment: EnvironmentParameters
}

export type StructureType =
  | 'substrate'
  | 'die'
  | 'flip_chip_bump'
  | 'underfill'
  | 'solder_ball'
  | 'solder_ball_matrix'
  | 'thermal_interface'
  | 'heat_slug'
  | 'lid'

export interface AxisAlignedBlock {
  id: string
  name: string
  structure_type: StructureType
  origin: { x: number; y: number; z: number }
  size: { x: number; y: number; z: number }
  material_id: string
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
  schema_version: 'packstudio.model/v1'
  template_id: 'flip-chip-cbga'
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
