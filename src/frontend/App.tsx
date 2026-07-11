import {
  AppBar,
  Box,
  Chip,
  CssBaseline,
  ThemeProvider,
  Toolbar,
  Typography,
  createTheme,
} from '@mui/material'

import Workspace from './features/flip-chip-cbga/Workspace'

const theme = createTheme({
  palette: {
    primary: { main: '#087f9c' },
    background: { default: '#f4f7f9' },
  },
  typography: {
    fontFamily: 'Inter, "Microsoft YaHei", system-ui, sans-serif',
  },
})

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box className="app-shell">
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" component="h1">
                PackStudio
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.82 }}>
                参数化 IC 封装热模型
              </Typography>
            </Box>
            <Chip label="TASK2 · Flip Chip CBGA" color="default" size="small" />
          </Toolbar>
        </AppBar>
        <Workspace />
      </Box>
    </ThemeProvider>
  )
}
