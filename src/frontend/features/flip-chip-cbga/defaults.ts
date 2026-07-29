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
const air = material('air', 'Air', 0.026, 1.225, 1005, '#DDEAF2')
const encapsulant = material(
  'encapsulant',
  'Epoxy molding compound (typical)',
  0.9,
  1900,
  1000,
  '#5A5AA8',
)
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
  encapsulant: {
    enabled: false,
    length: 5,
    width: 5,
    cover_thickness: 0.3,
    material: encapsulant,
  },
  flip_chip_bumps: {
    rows: 7,
    columns: 7,
    pitch_x: 0.25,
    pitch_y: 0.25,
    diameter: 0.12,
    height: 0.1,
    footprint_x_override: 1.8,
    footprint_y_override: 1.8,
    representation: 'equivalent',
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
    footprint_x_override: null,
    footprint_y_override: null,
    representation: 'equivalent',
    center_solder_enabled: false,
    center_solder_rows: 3,
    center_solder_columns: 3,
    solder_removal_enabled: false,
    removal_rows: 5,
    removal_columns: 5,
    omitted_cells: [],
    element_material: solder,
    matrix_material: air,
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
  mesh: { resolution: 'standard' },
  environment: {
    ambient_temperature_k: 300,
    default_convection_coefficient_w_m2k: 10,
    pcb_convection_coefficient_w_m2k: 1600,
    top_convection_coefficient_w_m2k: 10,
  },
}

export const createDefaultParameters = (): FlipChipCbgaParameters => structuredClone(defaults)
