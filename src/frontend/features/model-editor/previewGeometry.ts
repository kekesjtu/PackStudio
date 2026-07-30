import type { AxisAlignedBlock } from './types'

export interface BlockTransform {
  position: [number, number, number]
  size: [number, number, number]
}

export function toNativeXyzBlockTransform(block: AxisAlignedBlock): BlockTransform {
  return {
    position: [
      block.origin.x + block.size.x / 2,
      block.origin.y + block.size.y / 2,
      block.origin.z + block.size.z / 2,
    ],
    size: [block.size.x, block.size.y, block.size.z],
  }
}
