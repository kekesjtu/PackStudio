import type { FlipChipCbgaParameters, Material } from './types'

const material = (
  id: string,
  name: string,
  conductivity: number,
  density: number,
  specificHeat: number,
  color: string,
): Material => ({
  id,
  name,
  conductivity: { x: conductivity, y: conductivity, z: conductivity },
  density,
  specific_heat: specificHeat,
  color,
})

const alumina = material('alumina', 'Alumina (typical)', 25, 3900, 880, '#6975DC')
const silicon = material('silicon', 'Silicon', 130, 2330, 700, '#A33BD0')
const solder = material('solder', 'Solder (typical)', 50, 8400, 230, '#4A82D8')
const underfill = material(
  'underfill',
  'Flip-chip underfill (typical)',
  0.8,
  1600,
  1000,
  '#7CC5B8',
)
const copper = material('copper', 'Copper', 400, 8960, 385, '#C87533')
const tim = material('tim', 'Thermal interface material', 3, 2500, 1000, '#E1B84B')

const defaults: FlipChipCbgaParameters = {
  design_name: 'Flip Chip CBGA',
  substrate: { length: 6, width: 6, thickness: 1.15, material: alumina },
  die: { length: 1.8, width: 1.8, thickness: 0.61, power_w: 1, material: silicon },
  flip_chip_bumps: {
    rows: 7,
    columns: 7,
    pitch_x: 0.25,
    pitch_y: 0.25,
    diameter: 0.12,
    height: 0.1,
    representation: 'equivalent',
    pattern: 'full',
    center_rows: 0,
    center_columns: 0,
    omitted_cells: [],
    void_fill: 'matrix',
    emit_matrix_blocks: true,
    element_material: solder,
    matrix_material: underfill,
  },
  solder_balls: {
    rows: 7,
    columns: 7,
    pitch_x: 0.8,
    pitch_y: 0.8,
    diameter: 0.5,
    height: 0.4,
    representation: 'equivalent',
    pattern: 'center_populated',
    center_rows: 3,
    center_columns: 3,
    omitted_cells: [],
    void_fill: 'matrix',
    emit_matrix_blocks: true,
    element_material: solder,
    matrix_material: underfill,
  },
  heat_slug: {
    enabled: false,
    length: 2.4,
    width: 2.4,
    thickness: 0.25,
    material: copper,
    interface_thickness: 0.05,
    interface_material: tim,
  },
  lid: {
    enabled: false,
    length: 5.5,
    width: 5.5,
    thickness: 0.3,
    material: copper,
    interface_thickness: 0.05,
    interface_material: tim,
  },
  environment: {
    ambient_temperature_k: 300,
    bottom_convection_coefficient_w_m2k: null,
    top_convection_coefficient_w_m2k: null,
  },
}

export const createDefaultParameters = (): FlipChipCbgaParameters => structuredClone(defaults)
