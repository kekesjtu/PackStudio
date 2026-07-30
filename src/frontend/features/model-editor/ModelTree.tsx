import { useState, type MouseEvent } from 'react'
import {
  Box,
  Button,
  ButtonBase,
  Chip,
  Menu,
  MenuItem,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
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
  children?: React.ReactNode
}

function TreeNode(props: NodeProps) {
  const visibleCount = props.blockIds.filter((id) => !props.hiddenBlockIds.has(id)).length
  const allHidden = props.blockIds.length > 0 && visibleCount === 0
  return (
    <Box className="tree-group" sx={{ '--tree-depth': props.depth }}>
      <Stack direction="row" spacing={0.75} alignItems="center" className="tree-group-label">
        <Typography variant="body2" fontWeight={700} className="tree-group-name">
          {props.label}
        </Typography>
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
      {props.children}
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
  const childGroups = props.data.children.get(props.group.id) ?? []
  const blockIds = props.data.descendantIds.get(props.group.id) ?? []
  return (
    <TreeNode {...props} label={props.group.name} blockIds={blockIds}>
      <BlockRows {...props} blockIds={props.group.block_ids} />
      {childGroups.map((group) => (
        <GroupNode key={group.id} {...props} group={group} depth={props.depth + 1} />
      ))}
    </TreeNode>
  )
}

export default function ModelTree(props: ModelTreeProps) {
  const [mode, setMode] = useState<'components' | 'layers'>('components')
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
  if (!props.model) {
    return <Typography color="text.secondary">尚未生成模型。</Typography>
  }

  const data = buildTreeData(props.model)
  const rootGroups = data.children.get(null) ?? []
  const layers = buildLayers(props.model.blocks)
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
      <ToggleButtonGroup
        exclusive
        fullWidth
        size="small"
        value={mode}
        className="tree-view-mode"
        onChange={(_event, value: 'components' | 'layers' | null) => {
          if (value) setMode(value)
        }}
      >
        <ToggleButton value="components">组件层级</ToggleButton>
        <ToggleButton value="layers">Layer 层级</ToggleButton>
      </ToggleButtonGroup>
      {mode === 'components'
        ? rootGroups.map((group) => (
            <GroupNode key={group.id} {...nodeProps} group={group} depth={0} />
          ))
        : layers.map((layer) => (
            <TreeNode
              key={layer.key}
              {...nodeProps}
              label={layer.label}
              blockIds={layer.blockIds}
              depth={0}
            >
              <BlockRows {...nodeProps} blockIds={layer.blockIds} />
            </TreeNode>
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

function buildLayers(blocks: AxisAlignedBlock[]) {
  const grouped = new Map<string, { z0: number; z1: number; blockIds: string[] }>()
  for (const block of blocks) {
    const z0 = block.origin.z
    const z1 = z0 + block.size.z
    const key = `${z0.toFixed(9)}:${z1.toFixed(9)}`
    const layer = grouped.get(key) ?? { z0, z1, blockIds: [] }
    layer.blockIds.push(block.id)
    grouped.set(key, layer)
  }
  return [...grouped.entries()]
    .sort(([, left], [, right]) => right.z0 - left.z0 || right.z1 - left.z1)
    .map(([key, layer], index) => ({
      key,
      blockIds: layer.blockIds,
      label: `Layer ${index + 1} · z ${format(layer.z0)}–${format(layer.z1)} mm`,
    }))
}

const format = (value: number) => Number(value.toFixed(6)).toString()
