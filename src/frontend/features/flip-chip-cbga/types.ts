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

export interface EncapsulantParameters {
  enabled: boolean
  length: number
  width: number
  cover_thickness: number
  material: Material
}

export type ArrayRepresentation = 'discrete' | 'equivalent'

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
  footprint_x_override: number | null
  footprint_y_override: number | null
  representation: ArrayRepresentation
  element_material: Material
  matrix_material: Material
}

export interface SolderBallParameters extends ArrayLayerParameters {
  center_solder_enabled: boolean
  center_solder_rows: number
  center_solder_columns: number
  solder_removal_enabled: boolean
  removal_rows: number
  removal_columns: number
  omitted_cells: CellIndex[]
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
  default_convection_coefficient_w_m2k: number
  pcb_convection_coefficient_w_m2k: number
  top_convection_coefficient_w_m2k: number
}

export type MeshResolution = 'coarse' | 'standard' | 'fine'

export interface MeshParameters {
  resolution: MeshResolution
}

export interface FlipChipCbgaParameters {
  design_name: string
  substrate: RectangularPartParameters
  die: DieParameters
  encapsulant: EncapsulantParameters
  flip_chip_bumps: ArrayLayerParameters
  solder_balls: SolderBallParameters
  heat_slug: HeatSlugParameters
  lid: LidParameters
  mesh: MeshParameters
  environment: EnvironmentParameters
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
