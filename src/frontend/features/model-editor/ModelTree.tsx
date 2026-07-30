import { useState, type MouseEvent } from 'react'
import {
  Box,
  Button,
  ButtonBase,
  Chip,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from '@mui/material'

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

interface TreeData {
  blocks: Map<string, AxisAlignedBlock>
  children: Map<string | null, ModelGroup[]>
  descendantIds: Map<string, string[]>
}

interface NodeProps {
  label: string
  blockIds: string[]
  depth: number
  data: TreeData
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string) => void
  onSetBlocksHidden: (blockIds: string[], hidden: boolean) => void
  onOpenContextMenu: (event: MouseEvent, blockId: string) => void
  expanded: boolean
  onToggle: () => void
  children?: React.ReactNode
}

function TreeNode(props: NodeProps) {
  const visibleCount = props.blockIds.filter((id) => !props.hiddenBlockIds.has(id)).length
  const allHidden = props.blockIds.length > 0 && visibleCount === 0
  return (
    <Box className="tree-group" sx={{ '--tree-depth': props.depth }}>
      <Stack direction="row" spacing={0.75} alignItems="center" className="tree-group-label">
        <ButtonBase
          className="tree-group-toggle"
          aria-expanded={props.expanded}
          aria-label={`${props.expanded ? '折叠' : '展开'} ${props.label}`}
          onClick={props.onToggle}
        >
          <span className="tree-group-chevron" aria-hidden="true">
            {props.expanded ? '▾' : '▸'}
          </span>
          <Typography
            component="span"
            variant="body2"
            fontWeight={700}
            className="tree-group-name"
          >
            {props.label}
          </Typography>
        </ButtonBase>
        <Chip
          label={`${visibleCount}/${props.blockIds.length}`}
          size="small"
          variant="outlined"
        />
        {props.blockIds.length > 0 && (
          <Button
            size="small"
            onClick={() => props.onSetBlocksHidden(props.blockIds, !allHidden)}
            aria-label={`${allHidden ? '显示' : '隐藏'} ${props.label}`}
          >
            {allHidden ? '显示' : '隐藏'}
          </Button>
        )}
      </Stack>
      {props.expanded && props.children}
    </Box>
  )
}

function BlockRows(props: {
  blockIds: string[]
  data: TreeData
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string) => void
  onOpenContextMenu: (event: MouseEvent, blockId: string) => void
}) {
  return props.blockIds.map((blockId) => {
    const block = props.data.blocks.get(blockId)
    if (!block) return null
    const hidden = props.hiddenBlockIds.has(block.id)
    return (
      <ButtonBase
        key={block.id}
        className="tree-block"
        data-selected={block.id === props.selectedBlockId}
        data-hidden={hidden}
        onClick={() => props.onSelectBlock(block.id)}
        onContextMenu={(event) => props.onOpenContextMenu(event, block.id)}
      >
        <span>{block.name}</span>
        {hidden && <small>已隐藏</small>}
      </ButtonBase>
    )
  })
}

function GroupNode(props: {
  group: ModelGroup
  depth: number
  data: TreeData
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string) => void
  onSetBlocksHidden: (blockIds: string[], hidden: boolean) => void
  onOpenContextMenu: (event: MouseEvent, blockId: string) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const childGroups = props.data.children.get(props.group.id) ?? []
  const blockIds = props.data.descendantIds.get(props.group.id) ?? []
  return (
    <TreeNode
      {...props}
      label={props.group.name}
      blockIds={blockIds}
      expanded={expanded}
      onToggle={() => setExpanded((current) => !current)}
    >
      <BlockRows {...props} blockIds={props.group.block_ids} />
      {childGroups.map((group) => (
        <GroupNode key={group.id} {...props} group={group} depth={props.depth + 1} />
      ))}
    </TreeNode>
  )
}

export default function ModelTree(props: ModelTreeProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
  if (!props.model) {
    return <Typography color="text.secondary">尚未生成模型。</Typography>
  }

  const data = buildTreeData(props.model)
  const rootGroups = data.children.get(null) ?? []
  const closeMenu = () => setContextMenu(null)
  const setBlocksHidden = (blockIds: string[], hidden: boolean) => {
    for (const blockId of blockIds) props.onSetBlockHidden(blockId, hidden)
  }
  const openContextMenu = (event: MouseEvent, blockId: string) => {
    event.preventDefault()
    setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6, blockId })
  }
  const runContextAction = (action: (blockId: string) => void) => {
    if (contextMenu) action(contextMenu.blockId)
    closeMenu()
  }
  const contextBlockHidden =
    contextMenu !== null && props.hiddenBlockIds.has(contextMenu.blockId)
  const nodeProps = {
    data,
    selectedBlockId: props.selectedBlockId,
    hiddenBlockIds: props.hiddenBlockIds,
    onSelectBlock: props.onSelectBlock,
    onSetBlocksHidden: setBlocksHidden,
    onOpenContextMenu: openContextMenu,
  }

  return (
    <Box className="model-tree">
      {rootGroups.map((group) => (
        <GroupNode key={group.id} {...nodeProps} group={group} depth={0} />
      ))}
      <Menu
        open={contextMenu !== null}
        onClose={closeMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
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

function buildTreeData(model: PackageModel): TreeData {
  const children = new Map<string | null, ModelGroup[]>()
  for (const group of model.groups) {
    const items = children.get(group.parent_id) ?? []
    items.push(group)
    children.set(group.parent_id, items)
  }
  const descendantIds = new Map<string, string[]>()
  const collect = (group: ModelGroup): string[] => {
    const ids = [
      ...group.block_ids,
      ...(children.get(group.id) ?? []).flatMap((child) => collect(child)),
    ]
    descendantIds.set(group.id, ids)
    return ids
  }
  for (const root of children.get(null) ?? []) collect(root)
  return {
    blocks: new Map(model.blocks.map((block) => [block.id, block])),
    children,
    descendantIds,
  }
}
