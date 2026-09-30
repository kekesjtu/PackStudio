import {
  AppBar,
  Box,
  CssBaseline,
  MenuItem,
  Select,
  ThemeProvider,
  Toolbar,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'

import { loadTemplateCatalog } from './features/package-library/api'
import PackageWorkspace from './features/package-library/PackageWorkspace'
import type { TemplateCatalogItem } from './features/package-library/types'
import industrialTheme from './industrialTheme'

export default function App() {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([])
  const [templateId, setTemplateId] = useState('flip_chip_cbga')

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
              <Typography variant="caption" sx={{ opacity: 0.82 }}>
                参数化 IC 封装热模型
              </Typography>
            </Box>
            <Select
              size="small"
              value={templateId}
              aria-label="选择封装模板"
              onChange={(event) => setTemplateId(event.target.value)}
              sx={{
                minWidth: 290,
                backgroundColor: '#253f52',
                color: 'white',
                '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,.55)' },
                '.MuiSvgIcon-root': { color: 'white' },
              }}
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
  { id: 'flip_chip_cbga', display_name: 'Flip Chip CBGA' },
  { id: 'flip_chip_pbga', display_name: 'Flip Chip PBGA' },
  { id: 'wirebond_pbga', display_name: 'Wirebond PBGA' },
  { id: 'fbga_fsbga', display_name: 'FBGA / FSBGA' },
  { id: 'qfn', display_name: 'QFN' },
  { id: 'qfp_family', display_name: 'QFP family' },
  { id: 'soic_family', display_name: 'SOIC family' },
  { id: 'bare_die', display_name: 'Bare Die' },
]
