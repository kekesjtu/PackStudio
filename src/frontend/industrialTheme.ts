import { createTheme } from '@mui/material'

const industrialTheme = createTheme({
  palette: {
    primary: { main: '#255b80' },
    secondary: { main: '#5a6974' },
    background: { default: '#d7dce0', paper: '#f1f2f3' },
    text: { primary: '#27343e', secondary: '#586773' },
    divider: '#b6c0c8',
  },
  shape: { borderRadius: 2 },
  typography: {
    fontFamily: '"Segoe UI", "Microsoft YaHei", sans-serif',
    fontSize: 12,
    h5: { fontSize: '0.9rem', fontWeight: 600 },
    h6: { fontSize: '1rem', fontWeight: 600, letterSpacing: '0.02em' },
    subtitle2: { fontSize: '0.8rem', fontWeight: 600 },
    button: { textTransform: 'none', fontSize: '0.75rem', fontWeight: 500 },
  },
  components: {
    MuiAppBar: {
      styleOverrides: { root: { background: '#314c60', borderBottom: '1px solid #1c3345' } },
    },
    MuiToolbar: {
      styleOverrides: { root: { minHeight: '52px !important', paddingLeft: '14px !important' } },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: { root: { backgroundImage: 'none', border: '1px solid #aebbc5' } },
    },
    MuiButton: {
      defaultProps: { disableElevation: true, size: 'small' },
      styleOverrides: {
        root: { minHeight: 29, padding: '4px 9px', whiteSpace: 'nowrap' },
        outlined: { backgroundColor: '#f8f9fa', borderColor: '#9baab5' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { backgroundColor: '#fff', fontSize: '0.8rem' },
        input: { padding: '8px 10px', fontVariantNumeric: 'tabular-nums' },
        notchedOutline: { borderColor: '#aeb9c2' },
      },
    },
    MuiInputLabel: { styleOverrides: { root: { fontSize: '0.8rem' } } },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            backgroundColor: '#dae7ef',
            boxShadow: 'inset 3px 0 #255b80',
            '&:hover': { backgroundColor: '#cfdfeb' },
          },
        },
      },
    },
    MuiTabs: { styleOverrides: { root: { minHeight: 34 }, indicator: { height: 2 } } },
    MuiTab: { styleOverrides: { root: { minHeight: 34, padding: '6px 12px', fontWeight: 600 } } },
    MuiChip: { styleOverrides: { root: { height: 22, borderRadius: 2, fontSize: '0.7rem' } } },
    MuiAlert: { styleOverrides: { root: { border: '1px solid #b6c8d4', padding: '2px 10px' } } },
    MuiCheckbox: { styleOverrides: { root: { padding: 5 } } },
    MuiMenuItem: { styleOverrides: { root: { minHeight: 30, fontSize: '0.8rem' } } },
  },
})

export default industrialTheme
