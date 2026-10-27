import type { Material, PackageModel } from '../model-editor/types'

export type WizardValue = string | number | boolean | null

export interface CellIndex {
  row: number
  column: number
}

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
  unit?: string | null
  minimum?: number | null
  maximum?: number | null
  options: WizardValue[]
  option_labels?: Record<string, string>
  preset_values?: Record<string, Record<string, WizardValue>>
  preset_bga?: Record<string, BgaConfiguration>
  preset_notes?: Record<string, string>
  preset_materials?: Record<string, Record<string, string>>
  classification: string
  property_name: string | null
  supported_values: WizardValue[]
  evidence_status: 'implemented'
  editable: boolean
  material_group_id?: string | null
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
    outline_type: 'standard_outline'
    die_type: 'actual_type'
    bga_pattern: string | null
    flip_chip_bumps: string | null
  }
}

export interface BgaConfiguration {
  depopulated_center?: boolean | null
  staggered?: boolean
  center_staggered?: boolean
  populated_rows?: number | null
  populated_columns?: number | null
  ball_map_enabled?: boolean
  ball_map?: Array<{ id: string; x: number; y: number }>
  allow_asymmetric_regions?: boolean
  representation: 'equivalent' | 'discrete'
  center_solder_enabled: boolean
  center_solder_rows: number | null
  center_solder_columns: number | null
  solder_removal_enabled: boolean
  removal_rows: number | null
  removal_columns: number | null
  omitted_cells: CellIndex[]
}

export interface TemplateRequest {
  summary?: { part_number?: string; vendor?: string; max_power_w?: number | null;
    max_junction_temperature_c?: number | null; max_case_temperature_c?: number | null; notes?: string }
  template_id: string
  design_name: string | null
  overrides: Record<string, WizardValue>
  bga: BgaConfiguration | null
  vias?: ViaConfiguration | null
  material_assignments: Record<string, string>
  custom_materials: Material[]
  die_power_w: number | null
}

export interface ViaConfiguration {
  removal_enabled: boolean
  removal_rows: number | null
  removal_columns: number | null
  omitted_cells: CellIndex[]
}

export type { Material, PackageModel }
