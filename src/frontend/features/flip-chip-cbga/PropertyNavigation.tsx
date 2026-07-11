import {
  Alert,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material'

import { propertySections, type PropertySectionId } from './propertySections'

interface PropertyNavigationProps {
  activeSection: PropertySectionId
  onChange: (section: PropertySectionId) => void
}

export default function PropertyNavigation({
  activeSection,
  onChange,
}: PropertyNavigationProps) {
  return (
    <Paper component="nav" className="structure-navigation" aria-label="封装结构属性">
      <Typography variant="overline" color="text.secondary">
        当前模板
      </Typography>
      <Typography variant="h6">Flip Chip CBGA</Typography>
      <Typography variant="body2" color="text.secondary">
        选择结构以编辑属性
      </Typography>
      <Divider />
      <List disablePadding dense>
        {propertySections.map((section) => (
          <ListItemButton
            key={section.id}
            selected={section.id === activeSection}
            onClick={() => onChange(section.id)}
          >
            <ListItemText primary={section.label} />
          </ListItemButton>
        ))}
      </List>
      <Alert severity="info" icon={false} className="export-note">
        PTA 文件不包含网格和求解结果。
      </Alert>
    </Paper>
  )
}
