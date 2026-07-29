import type { FlipChipCbgaParameters } from './types'

export interface PackagePreset {
  id: string
  label: string
  ballCount: number
  packageLength: number
  packageWidth: number
  ballRows: number
  ballColumns: number
  ballPitch: 0.8 | 1 | 1.27
}

export const packagePresets: PackagePreset[] = [
  preset('cbgafc-49-6x6', 'CBGAFC_49_6X6mm', 49, 6, 6, 7, 7, 0.8),
  preset('cbgafc-49-8x8', 'CBGAFC_49_8X8mm', 49, 8, 8, 7, 7, 1),
  preset('cbgafc-64-7x7', 'CBGAFC_64_7X7mm', 64, 7, 7, 8, 8, 0.8),
  preset('cbgafc-64-8x8', 'CBGAFC_64_8X8mm', 64, 8, 8, 8, 8, 0.8),
  preset('cbgafc-64-9x9', 'CBGAFC_64_9X9mm', 64, 9, 9, 8, 8, 1),
  preset('cbgafc-81-8x8', 'CBGAFC_81_8X8mm', 81, 8, 8, 9, 9, 0.8),
  preset('cbgafc-81-10x10', 'CBGAFC_81_10X10mm', 81, 10, 10, 9, 9, 1),
  preset('cbgafc-100-9x9', 'CBGAFC_100_9X9mm', 100, 9, 9, 10, 10, 0.8),
  preset('cbgafc-119-14x22', 'CBGAFC_119_14X22mm', 119, 14, 22, 17, 7, 1.27),
  preset('cbgafc-144-10x10', 'CBGAFC_144_10X10mm', 144, 10, 10, 12, 12, 0.8),
]

export function applyPackagePreset(
  parameters: FlipChipCbgaParameters,
  presetId: string,
): FlipChipCbgaParameters {
  const selected = packagePresets.find((item) => item.id === presetId)
  if (selected === undefined) return parameters

  const dieLength = round(selected.packageLength * 0.3)
  const dieWidth = round(selected.packageWidth * 0.3)
  const bumpPitch = 0.25
  const bumpColumns = fittedCellCount(dieLength, bumpPitch)
  const bumpRows = fittedCellCount(dieWidth, bumpPitch)
  const largePackage = Math.min(selected.packageLength, selected.packageWidth) > 10
  const encapsulantInset = largePackage ? 2 : 1
  const lidInset = largePackage ? 1 : 0.5
  const ballGeometry = geometryForBallPitch(selected.ballPitch)

  return {
    ...parameters,
    substrate: {
      ...parameters.substrate,
      length: selected.packageLength,
      width: selected.packageWidth,
      thickness: largePackage ? 1.5 : 1.15,
    },
    die: {
      ...parameters.die,
      length: dieLength,
      width: dieWidth,
      thickness: 0.61,
    },
    encapsulant: {
      ...parameters.encapsulant,
      length: selected.packageLength - encapsulantInset,
      width: selected.packageWidth - encapsulantInset,
      cover_thickness: 0.3,
    },
    flip_chip_bumps: {
      ...parameters.flip_chip_bumps,
      rows: bumpRows,
      columns: bumpColumns,
      pitch_x: bumpPitch,
      pitch_y: bumpPitch,
      diameter: 0.12,
      height: 0.1,
      footprint_x_override: dieLength,
      footprint_y_override: dieWidth,
      representation: 'equivalent',
    },
    solder_balls: {
      ...parameters.solder_balls,
      rows: selected.ballRows,
      columns: selected.ballColumns,
      pitch_x: selected.ballPitch,
      pitch_y: selected.ballPitch,
      diameter: ballGeometry.diameter,
      height: ballGeometry.height,
      footprint_x_override: null,
      footprint_y_override: null,
      center_solder_enabled: false,
      center_solder_rows: centeredSize(selected.ballRows, 4),
      center_solder_columns: centeredSize(selected.ballColumns, 4),
      solder_removal_enabled: false,
      removal_rows: centeredSize(selected.ballRows, 2),
      removal_columns: centeredSize(selected.ballColumns, 2),
      omitted_cells: [],
    },
    heat_slug: {
      ...parameters.heat_slug,
      length: round(dieLength * (4 / 3)),
      width: round(dieWidth * (4 / 3)),
      thickness: 0.25,
      interface_thickness: 0.05,
    },
    lid: {
      ...parameters.lid,
      length: selected.packageLength - lidInset,
      width: selected.packageWidth - lidInset,
      thickness: 0.3,
      interface_thickness: 0.05,
    },
  }
}

export function detectPackagePreset(parameters: FlipChipCbgaParameters): string | null {
  const current = geometrySignature(parameters)
  return (
    packagePresets.find(
      (item) => geometrySignature(applyPackagePreset(parameters, item.id)) === current,
    )?.id ?? null
  )
}

function preset(
  id: string,
  label: string,
  ballCount: number,
  packageLength: number,
  packageWidth: number,
  ballRows: number,
  ballColumns: number,
  ballPitch: PackagePreset['ballPitch'],
): PackagePreset {
  return {
    id,
    label,
    ballCount,
    packageLength,
    packageWidth,
    ballRows,
    ballColumns,
    ballPitch,
  }
}

function fittedCellCount(parentSize: number, pitch: number): number {
  return Math.max(1, Math.floor((parentSize - 0.05) / pitch))
}

function centeredSize(total: number, borderCells: number): number {
  return Math.max(1, total - borderCells)
}

function geometryForBallPitch(pitch: PackagePreset['ballPitch']) {
  if (pitch === 0.8) return { diameter: 0.5, height: 0.4 }
  if (pitch === 1) return { diameter: 0.6, height: 0.5 }
  return { diameter: 0.75, height: 0.6 }
}

function geometrySignature(parameters: FlipChipCbgaParameters): string {
  const { substrate, die, encapsulant, flip_chip_bumps, solder_balls, heat_slug, lid } = parameters
  return JSON.stringify([
    substrate.length,
    substrate.width,
    substrate.thickness,
    die.length,
    die.width,
    die.thickness,
    encapsulant.length,
    encapsulant.width,
    encapsulant.cover_thickness,
    ...arrayGeometry(flip_chip_bumps),
    ...arrayGeometry(solder_balls),
    heat_slug.length,
    heat_slug.width,
    heat_slug.thickness,
    heat_slug.interface_thickness,
    lid.length,
    lid.width,
    lid.thickness,
    lid.interface_thickness,
  ])
}

function arrayGeometry(array: FlipChipCbgaParameters['flip_chip_bumps']): number[] {
  return [
    array.rows,
    array.columns,
    array.pitch_x,
    array.pitch_y,
    array.diameter,
    array.height,
  ]
}

const round = (value: number) => Math.round(value * 100) / 100
