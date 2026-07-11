import { Box, ButtonBase, Chip, Stack, Typography } from '@mui/material'

import type { AxisAlignedBlock, ModelGroup, PackageModel } from './types'

interface ModelTreeProps {
  model: PackageModel | null
  selectedBlockId: string | null
  onSelectBlock: (blockId: string) => void
}

interface GroupNodeProps {
  group: ModelGroup
  groups: ModelGroup[]
  blocks: Map<string, AxisAlignedBlock>
  depth: number
  selectedBlockId: string | null
  onSelectBlock: (blockId: string) => void
}

function GroupNode({
  group,
  groups,
  blocks,
  depth,
  selectedBlockId,
  onSelectBlock,
}: GroupNodeProps) {
  const children = groups.filter((candidate) => candidate.parent_id === group.id)

  return (
    <Box className="tree-group" sx={{ '--tree-depth': depth }}>
      <Stack direction="row" spacing={1} alignItems="center" className="tree-group-label">
        <Typography variant="body2" fontWeight={700}>
          {group.name}
        </Typography>
        <Chip label={group.block_ids.length} size="small" variant="outlined" />
      </Stack>
      {group.block_ids.map((blockId) => {
        const block = blocks.get(blockId)
        if (block === undefined) return null
        return (
          <ButtonBase
            key={block.id}
            className="tree-block"
            data-selected={block.id === selectedBlockId}
            onClick={() => onSelectBlock(block.id)}
          >
            <span>{block.name}</span>
            <small>{block.structure_type}</small>
          </ButtonBase>
        )
      })}
      {children.map((child) => (
        <GroupNode
          key={child.id}
          group={child}
          groups={groups}
          blocks={blocks}
          depth={depth + 1}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
        />
      ))}
    </Box>
  )
}

export default function ModelTree({ model, selectedBlockId, onSelectBlock }: ModelTreeProps) {
  if (model === null) {
    return <Typography color="text.secondary">尚未生成模型。</Typography>
  }

  const blocks = new Map(model.blocks.map((block) => [block.id, block]))
  const rootGroups = model.groups.filter((group) => group.parent_id === null)

  return (
    <Box className="model-tree">
      {rootGroups.map((group) => (
        <GroupNode
          key={group.id}
          group={group}
          groups={model.groups}
          blocks={blocks}
          depth={0}
          selectedBlockId={selectedBlockId}
          onSelectBlock={onSelectBlock}
        />
      ))}
    </Box>
  )
}
