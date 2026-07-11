import { useState, type MouseEvent } from 'react'
import { Box, ButtonBase, Chip, Menu, MenuItem, Stack, Typography } from '@mui/material'

import type { AxisAlignedBlock, ModelGroup, PackageModel } from './types'

interface ModelTreeProps {
  model: PackageModel | null
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string) => void
  onSetBlockHidden: (blockId: string, hidden: boolean) => void
  onShowOnlyBlock: (blockId: string) => void
  onShowAllBlocks: () => void
}

interface ContextMenuState {
  mouseX: number
  mouseY: number
  blockId: string
}

interface GroupNodeProps {
  group: ModelGroup
  groups: ModelGroup[]
  blocks: Map<string, AxisAlignedBlock>
  depth: number
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string) => void
  onOpenContextMenu: (event: MouseEvent, blockId: string) => void
}

function GroupNode({
  group,
  groups,
  blocks,
  depth,
  selectedBlockId,
  hiddenBlockIds,
  onSelectBlock,
  onOpenContextMenu,
}: GroupNodeProps) {
  const children = groups.filter((candidate) => candidate.parent_id === group.id)
  const visibleCount = group.block_ids.filter((id) => !hiddenBlockIds.has(id)).length

  return (
    <Box className="tree-group" sx={{ '--tree-depth': depth }}>
      <Stack direction="row" spacing={1} alignItems="center" className="tree-group-label">
        <Typography variant="body2" fontWeight={700}>
          {group.name}
        </Typography>
        <Chip label={`${visibleCount}/${group.block_ids.length}`} size="small" variant="outlined" />
      </Stack>
      {group.block_ids.map((blockId) => {
        const block = blocks.get(blockId)
        if (block === undefined) return null
        const hidden = hiddenBlockIds.has(block.id)
        return (
          <ButtonBase
            key={block.id}
            className="tree-block"
            data-selected={block.id === selectedBlockId}
            data-hidden={hidden}
            onClick={() => onSelectBlock(block.id)}
            onContextMenu={(event) => onOpenContextMenu(event, block.id)}
          >
            <span>{block.name}</span>
            <small>{hidden ? `已隐藏 · ${block.structure_type}` : block.structure_type}</small>
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
          hiddenBlockIds={hiddenBlockIds}
          onSelectBlock={onSelectBlock}
          onOpenContextMenu={onOpenContextMenu}
        />
      ))}
    </Box>
  )
}

export default function ModelTree(props: ModelTreeProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
  if (props.model === null) {
    return <Typography color="text.secondary">尚未生成模型。</Typography>
  }

  const blocks = new Map(props.model.blocks.map((block) => [block.id, block]))
  const rootGroups = props.model.groups.filter((group) => group.parent_id === null)
  const contextBlockHidden =
    contextMenu !== null && props.hiddenBlockIds.has(contextMenu.blockId)
  const closeMenu = () => setContextMenu(null)
  const runContextAction = (action: (blockId: string) => void) => {
    if (contextMenu !== null) action(contextMenu.blockId)
    closeMenu()
  }

  return (
    <Box className="model-tree">
      <Typography variant="caption" color="text.secondary">
        右键模型可隐藏、独显或恢复全部。
      </Typography>
      {rootGroups.map((group) => (
        <GroupNode
          key={group.id}
          group={group}
          groups={props.model?.groups ?? []}
          blocks={blocks}
          depth={0}
          selectedBlockId={props.selectedBlockId}
          hiddenBlockIds={props.hiddenBlockIds}
          onSelectBlock={props.onSelectBlock}
          onOpenContextMenu={(event, blockId) => {
            event.preventDefault()
            setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6, blockId })
          }}
        />
      ))}
      <Menu
        open={contextMenu !== null}
        onClose={closeMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu === null
            ? undefined
            : { top: contextMenu.mouseY, left: contextMenu.mouseX }
        }
      >
        <MenuItem
          onClick={() =>
            runContextAction((blockId) =>
              props.onSetBlockHidden(blockId, !contextBlockHidden),
            )
          }
        >
          {contextBlockHidden ? '显示这个模型' : '隐藏这个模型'}
        </MenuItem>
        <MenuItem onClick={() => runContextAction(props.onShowOnlyBlock)}>
          只显示这个模型
        </MenuItem>
        <MenuItem
          onClick={() => {
            props.onShowAllBlocks()
            closeMenu()
          }}
        >
          显示全部模型
        </MenuItem>
      </Menu>
    </Box>
  )
}
