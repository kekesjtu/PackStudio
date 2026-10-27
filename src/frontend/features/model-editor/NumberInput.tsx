import TextField from '@mui/material/TextField'

import FieldShell from '../../ui/FieldShell'
import numericInput from '../../ui/numericInput'

interface NumberInputProps {
  label: string
  value: number | null
  onChange: (value: number | null) => void
  unit?: string
  integer?: boolean
  allowEmpty?: boolean
}

export default function NumberInput({
  label,
  value,
  onChange,
  unit,
  integer = false,
  allowEmpty = false,
}: NumberInputProps) {
  return (
    <FieldShell label={label} unit={unit} className="field-shell-numeric">
      <TextField
        type="number"
        size="small"
        value={value ?? ''}
        onChange={(event) => {
          const rawValue = event.target.value
          if (rawValue === '' && allowEmpty) {
            onChange(null)
            return
          }
          const parsed = integer ? Number.parseInt(rawValue, 10) : Number(rawValue)
          onChange(Number.isFinite(parsed) ? parsed : 0)
        }}
        slotProps={{
          htmlInput: {
            'aria-label': label,
            ...numericInput(integer),
          },
        }}
        fullWidth
      />
    </FieldShell>
  )
}
