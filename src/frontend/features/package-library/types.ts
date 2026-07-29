import type {
  CellIndex,
  EnvironmentParameters,
  Material,
  MeshParameters,
  PackageModel,
} from '../flip-chip-cbga/types'

export type WizardValue = string | number | boolean | null

export interface TemplateCatalogItem {
  id: string
  display_name: string
  category: string
  has_bga: boolean
  bga_representations: Array<'equivalent' | 'discrete'>
  implementation_status: 'packstudio_native'
  runtime_reference_data_required: false
}

export interface WizardField {
  target_id: string
  ui_location: string
  component: string | null
  label: string
  control: string
  default: WizardValue
  options: WizardValue[]
  classification: string
  property_name: string | null
  supported_values: WizardValue[]
  evidence_status: 'implemented'
  editable: boolean
  visible_when?: Record<string, WizardValue>
  enabled_when?: Record<string, WizardValue>
  hidden_when?: Record<string, WizardValue>
}

export interface WizardStep {
  id: string
  label: string
  fields: WizardField[]
}

export interface TemplateSchema {
  schema_version: 'packstudio.wizard/v2'
  template_id: string
  steps: WizardStep[]
  has_bga: boolean
  special_rules: {
    bga_pattern: string | null
    flip_chip_bumps: string | null
  }
}

export interface BgaConfiguration {
  representation: 'equivalent' | 'discrete'
  center_solder_enabled: boolean
  center_solder_rows: number
  center_solder_columns: number
  solder_removal_enabled: boolean
  removal_rows: number
  removal_columns: number
  omitted_cells: CellIndex[]
}

export interface TemplateRequest {
  template_id: string
  design_name: string | null
  overrides: Record<string, WizardValue>
  bga: BgaConfiguration | null
  material_assignments: Record<string, string>
  custom_materials: Material[]
  die_power_w: number | null
  mesh: MeshParameters
  environment: EnvironmentParameters
}

export type { Material, PackageModel }
