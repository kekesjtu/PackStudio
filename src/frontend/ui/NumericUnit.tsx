import InputAdornment from '@mui/material/InputAdornment'

export default function NumericUnit({ unit }: { unit?: string | null }) {
  return unit ? (
    <InputAdornment position="end" className="numeric-unit" disablePointerEvents>
      {unit}
    </InputAdornment>
  ) : null
}
