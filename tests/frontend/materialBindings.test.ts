import { describe, expect, it } from 'vitest'

import { createDefaultParameters } from '../../src/frontend/features/flip-chip-cbga/defaults'
import {
  assignMaterialToSlot,
  collectMaterialLibrary,
  replaceMaterialDefinition,
} from '../../src/frontend/features/flip-chip-cbga/materialBindings'

describe('material bindings', () => {
  it('keeps shared material definitions unique in the library', () => {
    const library = collectMaterialLibrary(createDefaultParameters())

    expect(library.filter((material) => material.id === 'solder')).toHaveLength(1)
    expect(library.some((material) => material.id === 'encapsulant')).toBe(true)
  })

  it('propagates an edited material to every structure using its id', () => {
    const parameters = createDefaultParameters()
    const editedSolder = {
      ...parameters.solder_balls.element_material,
      density: 9100,
    }

    const updated = replaceMaterialDefinition(parameters, editedSolder)

    expect(updated.flip_chip_bumps.element_material.density).toBe(9100)
    expect(updated.solder_balls.element_material.density).toBe(9100)
  })

  it('can bind a library material to a rectangular structure', () => {
    const parameters = createDefaultParameters()

    const updated = assignMaterialToSlot(parameters, 'encapsulant', parameters.lid.material)

    expect(updated.encapsulant.material.id).toBe('copper')
    expect(updated.lid.material.id).toBe('copper')
  })
})
