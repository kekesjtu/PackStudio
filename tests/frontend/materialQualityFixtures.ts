import type {
  Material, PackageModel, TemplateRequest, TemplateSchema, WizardField,
} from '../../src/frontend/features/package-library/types'

export const suspect: Material = {
  id: 'adhesive', name: '芯片胶', conductivity: { x: 2.5, y: 2.5, z: 2.5 },
  density: 1, specific_heat: 1, color: '#aaaaaa',
}
export const safe: Material = { ...suspect, id: 'safe', name: '已补齐材料',
  density: 2200, specific_heat: 900 }
export const selection: WizardField = {
  target_id: 'sample.material.adhesive', label: '芯片胶材料', control: 'material',
  default: 'adhesive', material_group_id: 'group-adhesive',
  ui_location: 'adhesive', component: 'group-adhesive', options: ['adhesive', 'safe'],
  supported_values: ['adhesive', 'safe'], property_name: 'material.group-adhesive',
  classification: 'material_option', evidence_status: 'implemented', editable: true,
}
export const request: TemplateRequest = {
  template_id: 'sample', design_name: '示例', overrides: {}, bga: null,
  material_assignments: {}, custom_materials: [], die_power_w: null,
}
export const schema: TemplateSchema = {
  template_id: 'sample', schema_version: 'packstudio.wizard/v2', has_bga: false,
  steps: [{ id: 'adhesive', label: '芯片胶', fields: [selection] }],
  special_rules: { outline_type: 'standard_outline', die_type: 'actual_type',
    bga_pattern: null, flip_chip_bumps: null },
}
export const model: PackageModel = {
  template_id: 'sample', schema_version: 'packstudio.model/v1', name: '示例', length_unit: 'mm',
  coordinate_system: { origin: 'center', x_axis: 'x', y_axis: 'y', z_axis: 'z' },
  materials: [safe], blocks: [{ id: 'body', name: '实体', material_id: 'safe',
    structure_type: 'generic', parent_group_id: 'package', metadata: {},
    origin: { x: 0, y: 0, z: 0 }, size: { x: 1, y: 1, z: 1 } }],
  groups: [{ id: 'package', name: '封装', parent_id: null, block_ids: ['body'] }],
  heat_sources: [], boundaries: [], metadata: {},
}
