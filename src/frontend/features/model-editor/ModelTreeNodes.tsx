import type { MouseEvent } from 'react'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Chip from '@mui/material/Chip'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'

import type { TreeData, TreeTarget } from './modelTreeData'

interface TreeNodesProps {
  parentId: string | null
  data: TreeData
  selectedBlockIds: ReadonlySet<string>
  hiddenBlockIds: ReadonlySet<string>
  collapsedGroupIds: ReadonlySet<string>
  onSelectBlock: (event: MouseEvent, blockId: string) => void
  onToggleGroup: (groupId: string) => void
  onOpenContextMenu: (event: MouseEvent, target: TreeTarget | null) => void
}

export default function ModelTreeNodes(props: TreeNodesProps) {
  return (props.data.entries.get(props.parentId) ?? []).map((entry) => {
    if (entry.kind === 'block') {
      const { block } = entry
      const hidden = props.hiddenBlockIds.has(block.id)
      return (
        <ButtonBase key={`block:${block.id}`} className="tree-block"
          data-selected={props.selectedBlockIds.has(block.id)} data-hidden={hidden}
          aria-pressed={props.selectedBlockIds.has(block.id)}
          onClick={(event) => props.onSelectBlock(event, block.id)}
          onContextMenu={(event) => props.onOpenContextMenu(event,
            { kind: 'block', blockIds: [block.id] })}>
          <span>{block.name}</span>
          {hidden && <small>已隐藏</small>}
        </ButtonBase>
      )
    }
    const { group } = entry
    const blockIds = props.data.descendantIds.get(group.id) ?? []
    const visibleCount = blockIds.filter((id) => !props.hiddenBlockIds.has(id)).length
    const isRoot = props.parentId === null
    const expanded = isRoot || !props.collapsedGroupIds.has(group.id)
    const label = <Typography component="span" variant="body2" fontWeight={700} className="tree-group-name">
      {group.name}
    </Typography>
    return (
      <Box key={`group:${group.id}`} className="tree-group">
        <Stack direction="row" spacing={0.75} alignItems="center" className="tree-group-label"
          onContextMenu={(event) => props.onOpenContextMenu(event, { kind: 'group', blockIds })}>
          {isRoot ? <Box className="tree-group-title">{label}</Box> : (
            <ButtonBase className="tree-group-toggle" aria-expanded={expanded}
              aria-label={`${expanded ? '折叠' : '展开'} ${group.name}`}
              onClick={() => props.onToggleGroup(group.id)}>
              <span className="tree-group-chevron" aria-hidden="true">{expanded ? '−' : '+'}</span>
              {label}
            </ButtonBase>
          )}
          <Chip label={`${visibleCount}/${blockIds.length}`} size="small" variant="outlined" />
        </Stack>
        {expanded && <ModelTreeNodes {...props} parentId={group.id} />}
      </Box>
    )
  })
}
