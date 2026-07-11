import { describe, expect, it } from 'vitest'

import { toNativeXyzBlockTransform } from '../../src/frontend/features/flip-chip-cbga/previewGeometry'
import type { AxisAlignedBlock } from '../../src/frontend/features/flip-chip-cbga/types'

describe('3D preview coordinates', () => {
  it('keeps the domain XYZ axes without swapping or reflecting them', () => {
    const block: AxisAlignedBlock = {
      id: 'test-block',
      name: 'Test block',
      structure_type: 'substrate',
      origin: { x: 1, y: 2, z: 3 },
      size: { x: 2, y: 4, z: 6 },
      material_id: 'test-material',
      parent_group_id: 'test-group',
      metadata: {},
    }

    expect(toNativeXyzBlockTransform(block)).toEqual({
      position: [2, 4, 6],
      size: [2, 4, 6],
    })
  })
})
