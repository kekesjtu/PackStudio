import AppBar from '@mui/material/AppBar'
import Box from '@mui/material/Box'
import CssBaseline from '@mui/material/CssBaseline'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import { ThemeProvider } from '@mui/material/styles'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import { useEffect, useState } from 'react'

import { loadTemplateCatalog } from './features/package-library/api'
import PackageWorkspace from './features/package-library/PackageWorkspace'
import type { TemplateCatalogItem } from './features/package-library/types'
import industrialTheme from './industrialTheme'

export default function App() {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([])
  const [templateId, setTemplateId] = useState('cbga_fc')

  useEffect(() => {
    loadTemplateCatalog().then(setTemplates).catch(() => setTemplates([]))
  }, [])

  return (
    <ThemeProvider theme={industrialTheme}>
      <CssBaseline />
      <Box className="app-shell">
        <AppBar position="static" elevation={0}>
          <Toolbar sx={{ gap: 2 }}>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" component="h1">
                PackStudio
              </Typography>
              <Typography variant="caption" className="appbar-eyebrow">
                参数化 IC 封装热模型
              </Typography>
            </Box>
            <Typography variant="caption" className="appbar-field-label">
              Package Types
            </Typography>
            <Select
              size="small"
              className="appbar-template-select"
              value={templateId}
              SelectDisplayProps={{ 'aria-label': 'Package Types' }}
              onChange={(event) => setTemplateId(event.target.value)}
              sx={{ minWidth: 290 }}
            >
              {(templates.length ? templates : fallbackTemplates).map((template) => (
                <MenuItem key={template.id} value={template.id}>
                  {template.display_name}
                </MenuItem>
              ))}
            </Select>
          </Toolbar>
        </AppBar>
        <PackageWorkspace key={templateId} templateId={templateId} />
      </Box>
    </ThemeProvider>
  )
}

const fallbackTemplates = [
  { id: 'chip_array', display_name: 'Chip Array' },
  { id: 'bare_die', display_name: 'Bare Die' },
  { id: 'cbga_fc', display_name: 'Flip Chip CBGA' },
  { id: 'pbga_fc', display_name: 'Flip Chip PBGA' },
  { id: 'pqfp', display_name: 'PQFP' },
  { id: 'qfn', display_name: 'QFN' },
  { id: 'sop', display_name: 'SOP' },
  { id: 'pbga_wb', display_name: 'Wirebond PBGA' },
]
