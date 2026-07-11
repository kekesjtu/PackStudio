import {
  AppBar,
  Box,
  Button,
  Chip,
  CssBaseline,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  TextField,
  ThemeProvider,
  Toolbar,
  Typography,
  createTheme,
} from '@mui/material'

const workflowSteps = ['选择模板', '封装参数', '材料', '热源与边界', '检查并导出']

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
            <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
              PackStudio
            </Typography>
            <Chip label="TASK1 项目骨架" color="default" size="small" />
          </Toolbar>
        </AppBar>

        <Box component="main" className="workspace">
          <Paper component="nav" className="workflow-panel" aria-label="建模步骤">
            <Typography variant="overline" color="text.secondary">
              建模流程
            </Typography>
            <List disablePadding>
              {workflowSteps.map((step, index) => (
                <ListItemButton key={step} selected={index === 1}>
                  <ListItemText primary={`${index + 1}. ${step}`} />
                </ListItemButton>
              ))}
            </List>
          </Paper>

          <Paper component="section" className="parameter-panel">
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="h5" component="h2">
                  封装参数
                </Typography>
                <Typography color="text.secondary">
                  当前页面用于验证前端脚手架，参数化模型将在后续阶段接入。
                </Typography>
              </Box>
              <Divider />
              <TextField label="设计名称" defaultValue="Flip Chip CBGA" fullWidth />
              <TextField label="基板长度" defaultValue="6" helperText="单位：mm" fullWidth />
              <TextField label="芯片功率" defaultValue="0" helperText="单位：W" fullWidth />
              <Button variant="contained" disabled>
                生成模型
              </Button>
            </Stack>
          </Paper>

          <Paper component="section" className="preview-panel">
            <Box>
              <Typography variant="h5" component="h2">
                三维预览
              </Typography>
              <Typography color="text.secondary">笛卡尔矩形块模型预览区域</Typography>
            </Box>
            <Box className="package-preview" aria-label="封装模型占位预览">
              <Box className="package-layer package-substrate" />
              <Box className="package-layer package-die" />
            </Box>
          </Paper>
        </Box>
      </Box>
    </ThemeProvider>
  )
}
