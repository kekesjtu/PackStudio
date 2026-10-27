import { useState, type MouseEvent } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import Typography from '@mui/material/Typography'

import ModelTreeNodes from './ModelTreeNodes'
import buildTreeData, { type TreeTarget } from './modelTreeData'
import type { PackageModel } from './types'

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
  target: TreeTarget | null
}

export default function ModelTree(props: ModelTreeProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
  const [collapsedGroupIds, setCollapsedGroupIds] = useState<Set<string>>(() => new Set())
  if (!props.model) return <Typography color="text.secondary">尚未生成模型。</Typography>

  const data = buildTreeData(props.model)
  const groupIds = props.model.groups.map((group) => group.id)
  const allCollapsed = groupIds.length > 0 && groupIds.every((id) => collapsedGroupIds.has(id))
  const closeMenu = () => setContextMenu(null)
  const openContextMenu = (event: MouseEvent, target: TreeTarget | null) => {
    event.preventDefault()
    event.stopPropagation()
    setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6, target })
  }
  const target = contextMenu?.target
  const targetHidden = target && target.blockIds.length > 0 &&
    target.blockIds.every((id) => props.hiddenBlockIds.has(id))
  const targetNoun = target?.kind === 'group' ? '这个分组' : '这个模型'
  const toggleTargetVisibility = () => {
    target?.blockIds.forEach((id) => props.onSetBlockHidden(id, !targetHidden))
    closeMenu()
  }
  const showOnlyTarget = () => {
    if (target?.kind === 'block') props.onShowOnlyBlock(target.blockIds[0])
    else if (target) {
      const ids = new Set(target.blockIds)
      props.model!.blocks.forEach((block) => props.onSetBlockHidden(block.id, !ids.has(block.id)))
    }
    closeMenu()
  }
  const toggleGroup = (groupId: string) => {
    setCollapsedGroupIds((current) => {
      const next = new Set(current)
      if (next.has(groupId)) next.delete(groupId)
      else next.add(groupId)
      return next
    })
  }

  return (
    <Box className="model-tree" role="region" aria-label="模型树"
      onContextMenu={(event) => openContextMenu(event, null)}>
      <Box className="model-tree-toolbar">
        <Button size="small" className="model-tree-toggle-all"
          aria-label={allCollapsed ? '全部展开' : '全部折叠'}
          title={allCollapsed ? '展开所有父节点' : '折叠所有父节点'}
          onClick={() => setCollapsedGroupIds(allCollapsed ? new Set() : new Set(groupIds))}>
          <span aria-hidden="true">{allCollapsed ? '⊞' : '⊟'}</span>
          {allCollapsed ? '全部展开' : '全部折叠'}
        </Button>
      </Box>
      <ModelTreeNodes parentId={null} data={data} selectedBlockId={props.selectedBlockId}
        hiddenBlockIds={props.hiddenBlockIds} collapsedGroupIds={collapsedGroupIds}
        onSelectBlock={props.onSelectBlock} onToggleGroup={toggleGroup}
        onOpenContextMenu={openContextMenu} />
      <Menu open={contextMenu !== null} onClose={closeMenu} anchorReference="anchorPosition"
        onContextMenu={(event) => { event.preventDefault(); event.stopPropagation() }}
        anchorPosition={contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}>
        {target && [
          <MenuItem key="visibility" disabled={target.blockIds.length === 0} onClick={toggleTargetVisibility}>
            {targetHidden ? '显示' : '隐藏'}{targetNoun}
          </MenuItem>,
          <MenuItem key="only" disabled={target.blockIds.length === 0} onClick={showOnlyTarget}>
            只显示{targetNoun}
          </MenuItem>,
          <Divider key="divider" />,
        ]}
        <MenuItem onClick={() => { props.onShowAllBlocks(); closeMenu() }}>显示全部模型</MenuItem>
        <MenuItem onClick={() => {
          props.model!.blocks.forEach((block) => props.onSetBlockHidden(block.id, true))
          closeMenu()
        }}>隐藏全部模型</MenuItem>
      </Menu>
    </Box>
  )
}
