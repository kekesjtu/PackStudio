import type { AxisAlignedBlock, ModelGroup, PackageModel } from './types'

export type TreeEntry =
  | { kind: 'block'; block: AxisAlignedBlock; z: number }
  | { kind: 'group'; group: ModelGroup; z: number }

export interface TreeData {
  entries: Map<string | null, TreeEntry[]>
  descendantIds: Map<string, string[]>
}

export interface TreeTarget {
  kind: 'block' | 'group'
  blockIds: string[]
}

export default function buildTreeData(model: PackageModel): TreeData {
  const blocks = new Map(model.blocks.map((block) => [block.id, block]))
  const groups = new Map(model.groups.map((group) => [group.id, group]))
  const children = new Map<string | null, ModelGroup[]>()
  for (const group of model.groups) {
    const items = children.get(group.parent_id) ?? []
    items.push(group)
    children.set(group.parent_id, items)
  }
  const descendantIds = new Map<string, string[]>()
  const collect = (group: ModelGroup): string[] => {
    const ids = [...new Set([
      ...group.block_ids.filter((id) => blocks.has(id)),
      ...(children.get(group.id) ?? []).flatMap(collect),
    ])]
    descendantIds.set(group.id, ids)
    return ids
  }
  for (const root of children.get(null) ?? []) collect(root)
  const centerZ = (ids: string[]) => {
    if (ids.length === 0) return -Infinity
    let bottom = Infinity
    let top = -Infinity
    for (const id of ids) {
      const block = blocks.get(id)!
      bottom = Math.min(bottom, block.origin.z)
      top = Math.max(top, block.origin.z + block.size.z)
    }
    return (bottom + top) / 2
  }
  const entries = new Map<string | null, TreeEntry[]>()
  for (const parent of [null, ...groups.keys()]) {
    const items: TreeEntry[] = (groups.get(parent ?? '')?.block_ids ?? []).flatMap((id) => {
      const block = blocks.get(id)
      return block ? [{ kind: 'block' as const, block, z: centerZ([id]) }] : []
    })
    for (const group of children.get(parent) ?? []) {
      items.push({ kind: 'group', group, z: centerZ(descendantIds.get(group.id) ?? []) })
    }
    // Stable sorting preserves source order for items at the same height.
    items.sort((left, right) => left.z === right.z ? 0 : left.z > right.z ? -1 : 1)
    entries.set(parent, items)
  }
  return { entries, descendantIds }
}
