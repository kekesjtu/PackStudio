import { createTheme } from '@mui/material/styles'

const labelFont = '"Bahnschrift", "Segoe UI", "Microsoft YaHei UI", sans-serif'
const textFont = '"Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif'

const industrialTheme = createTheme({
  palette: {
    primary: { main: '#2f6f92', dark: '#245773', light: '#4a8db3', contrastText: '#ffffff' },
    secondary: { main: '#5b6b75' },
    error: { main: '#b33b30' },
    warning: { main: '#b07a1f' },
    success: { main: '#3f7a57' },
    info: { main: '#356f8e' },
    background: { default: '#c9ced2', paper: '#f4f6f7' },
    text: { primary: '#1f2b33', secondary: '#5b6a73', disabled: '#9aa5ab' },
    divider: '#aeb8bf',
  },
  shape: { borderRadius: 0 },
  typography: {
    fontFamily: textFont,
    fontSize: 12,
    body1: { fontSize: '0.76rem', lineHeight: 1.5 },
    body2: { fontSize: '0.72rem', lineHeight: 1.5 },
    caption: { fontSize: '0.66rem', lineHeight: 1.45 },
    h5: { fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.05em' },
    h6: { fontSize: '0.95rem', fontWeight: 700, letterSpacing: '0.07em' },
    subtitle2: { fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.03em' },
    button: { textTransform: 'none', fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.02em' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#c9ced2',
          color: '#1f2b33',
          WebkitFontSmoothing: 'antialiased',
        },
        '::selection': { backgroundColor: '#cfe0ea' },
        '*': { scrollbarWidth: 'thin', scrollbarColor: '#98a5ad #dfe4e7' },
        '*::-webkit-scrollbar': { width: 12, height: 12 },
        '*::-webkit-scrollbar-track': { background: '#dfe4e7', borderLeft: '1px solid #c4ccd1' },
        '*::-webkit-scrollbar-thumb': {
          background: '#9aa7af',
          border: '2px solid #dfe4e7',
          borderRadius: 0,
        },
        '*::-webkit-scrollbar-thumb:hover': { background: '#7f8f99' },
        '*::-webkit-scrollbar-corner': { background: '#dfe4e7' },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          background: 'linear-gradient(#354d5d, #2a3f4d)',
          border: 0,
          boxShadow: 'inset 0 -2px 0 #162a36, inset 0 -3px 0 #4d7f9c',
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: '52px !important',
          paddingLeft: '12px !important',
          paddingRight: '12px !important',
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#f4f6f7',
          border: '1px solid #a9b3ba',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true, size: 'small' },
      styleOverrides: {
        root: {
          minHeight: 27,
          borderRadius: 0,
          padding: '3px 10px',
          whiteSpace: 'nowrap',
        },
        contained: {
          background: 'linear-gradient(#3d7ea6, #2f6584)',
          border: '1px solid #24506a',
          boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.2)',
          '&:hover': { background: 'linear-gradient(#347396, #285a76)' },
        },
        outlined: {
          background: 'linear-gradient(#fbfcfd, #edf1f3)',
          borderColor: '#9da9b1',
          color: '#263842',
          boxShadow: 'inset 0 1px 0 #ffffff',
          '&:hover': {
            borderColor: '#7c8c96',
            background: 'linear-gradient(#f6f9fa, #e6ebee)',
          },
        },
        text: { color: '#356f8e' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          backgroundColor: '#ffffff',
          fontSize: '0.75rem',
          boxShadow: 'inset 0 1px 2px rgba(22, 42, 54, 0.1)',
          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#8595a0' },
          '&.Mui-focused': { boxShadow: '0 0 0 1px #2f6f92, inset 0 1px 2px rgba(22, 42, 54, 0.1)' },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#2f6f92',
            borderWidth: 1,
          },
          '&.Mui-disabled': { backgroundColor: '#e8ebed', boxShadow: 'none' },
        },
        input: {
          height: '1.35em',
          padding: '6px 8px',
          fontVariantNumeric: 'tabular-nums',
        },
        notchedOutline: { borderRadius: 0, borderColor: '#a6b0b7' },
      },
    },
    MuiSelect: {
      styleOverrides: {
        icon: { right: 6, fontSize: 18, color: '#5b6a73' },
        select: { paddingRight: '26px !important' },
      },
    },
    MuiInputLabel: { styleOverrides: { root: { fontSize: '0.72rem' } } },
    MuiFormHelperText: {
      styleOverrides: {
        root: { margin: '2px 1px 0', fontSize: '0.64rem', lineHeight: 1.4, color: '#6a7a84' },
      },
    },
    MuiFormControlLabel: {
      styleOverrides: { label: { fontSize: '0.72rem', fontWeight: 600, color: '#34454f' } },
    },
    MuiSwitch: {
      defaultProps: { size: 'small' },
      styleOverrides: {
        switchBase: {
          '&.Mui-checked': { color: '#f4f6f7' },
          '&.Mui-checked + .MuiSwitch-track': { backgroundColor: '#2f6f92', opacity: 1 },
        },
        thumb: {
          borderRadius: 0,
          boxShadow: '0 0 0 1px rgba(22, 42, 54, 0.35)',
        },
        track: { borderRadius: 0, backgroundColor: '#9aa7af', opacity: 1 },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          minHeight: 26,
          padding: '3px 9px',
          '&:hover': { backgroundColor: '#e8edf0' },
          '&.Mui-selected': {
            backgroundColor: '#dce7ed',
            boxShadow: 'inset 3px 0 #2f6f92',
            '&:hover': { backgroundColor: '#d2e0e8' },
          },
        },
      },
    },
    MuiListItemText: {
      styleOverrides: {
        primary: { fontSize: '0.72rem', lineHeight: 1.4 },
        secondary: { fontSize: '0.64rem', lineHeight: 1.4 },
      },
    },
    MuiTabs: {
      styleOverrides: { root: { minHeight: 32 }, indicator: { height: 2, backgroundColor: '#2f6f92' } },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          minHeight: 32,
          padding: '5px 10px',
          fontSize: '0.72rem',
          fontWeight: 600,
          letterSpacing: '0.02em',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { height: 18, borderRadius: 0, fontSize: '0.62rem', fontWeight: 600 },
        label: { paddingLeft: 6, paddingRight: 6 },
        outlined: { borderColor: '#a3afb7', color: '#44545e', backgroundColor: '#f6f8f9' },
        colorWarning: {
          backgroundColor: '#f2e2c4',
          color: '#7a5410',
          border: '1px solid #d8bc84',
        },
        colorSuccess: {
          backgroundColor: '#dcecdf',
          color: '#2f5c3d',
          border: '1px solid #a9c6b1',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          alignItems: 'center',
          borderRadius: 0,
          border: '1px solid #b7c3cb',
          borderLeftWidth: 3,
          padding: '1px 9px',
          fontSize: '0.7rem',
        },
        message: { padding: '4px 0' },
        standardInfo: {
          backgroundColor: '#e8f0f5',
          borderColor: '#b6cbd8',
          color: '#26495e',
        },
        standardWarning: {
          backgroundColor: '#f7eeda',
          borderColor: '#ddc697',
          color: '#6b4c12',
        },
        standardError: {
          backgroundColor: '#f7e3e0',
          borderColor: '#d9b1aa',
          color: '#6f2b23',
        },
        standardSuccess: {
          backgroundColor: '#e4efe6',
          borderColor: '#b4cbb8',
          color: '#2f5839',
        },
      },
    },
    MuiCheckbox: { styleOverrides: { root: { padding: 4, borderRadius: 0 } } },
    MuiMenuItem: { styleOverrides: { root: { minHeight: 27, fontSize: '0.72rem' } } },
    MuiMenu: {
      styleOverrides: {
        paper: {
          border: '1px solid #9da9b1',
          borderRadius: 0,
          boxShadow: '2px 3px 8px rgba(22, 42, 54, 0.28)',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 0,
          backgroundColor: '#22333e',
          fontSize: '0.66rem',
          fontFamily: labelFont,
        },
      },
    },
  },
})

export default industrialTheme
