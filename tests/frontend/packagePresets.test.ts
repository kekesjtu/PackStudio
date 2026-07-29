import { describe, expect, it } from 'vitest'

import { createDefaultParameters } from '../../src/frontend/features/flip-chip-cbga/defaults'
import {
  applyPackagePreset,
  detectPackagePreset,
  packagePresets,
} from '../../src/frontend/features/flip-chip-cbga/packagePresets'

describe('Flip Chip CBGA package presets', () => {
  it('provides the ten reference footprints shown by FloTHERM PACK', () => {
    expect(packagePresets).toHaveLength(10)
    expect(packagePresets.map((preset) => preset.label)).toEqual([
      'CBGAFC_49_6X6mm',
      'CBGAFC_49_8X8mm',
      'CBGAFC_64_7X7mm',
      'CBGAFC_64_8X8mm',
      'CBGAFC_64_9X9mm',
      'CBGAFC_81_8X8mm',
      'CBGAFC_81_10X10mm',
      'CBGAFC_100_9X9mm',
      'CBGAFC_119_14X22mm',
      'CBGAFC_144_10X10mm',
    ])
  })

  it('keeps every derived array inside its parent geometry', () => {
    const defaults = createDefaultParameters()

    for (const preset of packagePresets) {
      const parameters = applyPackagePreset(defaults, preset.id)
      const balls = parameters.solder_balls
      const bumps = parameters.flip_chip_bumps

      expect(balls.rows * balls.columns).toBe(preset.ballCount)
      expect((balls.columns - 1) * balls.pitch_x + balls.diameter).toBeLessThanOrEqual(
        parameters.substrate.length,
      )
      expect((balls.rows - 1) * balls.pitch_y + balls.diameter).toBeLessThanOrEqual(
        parameters.substrate.width,
      )
      expect((bumps.columns - 1) * bumps.pitch_x + bumps.diameter).toBeLessThanOrEqual(
        parameters.die.length,
      )
      expect((bumps.rows - 1) * bumps.pitch_y + bumps.diameter).toBeLessThanOrEqual(
        parameters.die.width,
      )
      expect(bumps.footprint_x_override).toBe(parameters.die.length)
      expect(bumps.footprint_y_override).toBe(parameters.die.width)
      expect(parameters.encapsulant.length).toBeGreaterThan(parameters.die.length)
      expect(parameters.encapsulant.width).toBeGreaterThan(parameters.die.width)
      expect(detectPackagePreset(parameters)).toBe(preset.id)
    }
  })

  it('preserves the reviewed C4 density and fill fraction for every preset', () => {
    const defaults = createDefaultParameters()

    for (const preset of packagePresets) {
      const bumps = applyPackagePreset(defaults, preset.id).flip_chip_bumps
      const density = 1 / (bumps.pitch_x * bumps.pitch_y)
      const fillFraction =
        (Math.PI * (bumps.diameter / 2) ** 2) / (bumps.pitch_x * bumps.pitch_y)

      expect(density).toBeCloseTo(16)
      expect(fillFraction).toBeCloseTo(0.1809557368)
      expect(bumps.representation).toBe('equivalent')
    }
  })

  it('marks manually edited geometry as custom', () => {
    const parameters = createDefaultParameters()
    const edited = {
      ...parameters,
      die: { ...parameters.die, length: parameters.die.length + 0.1 },
    }

    expect(detectPackagePreset(parameters)).toBe('cbgafc-49-6x6')
    expect(detectPackagePreset(edited)).toBeNull()
  })
})
