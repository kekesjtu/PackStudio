import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import type { ReactNode } from 'react'

interface FieldShellProps {
  label: string
  unit?: string
  hint?: ReactNode
  disabled?: boolean
  className?: string
  children: ReactNode
}

/**
 * 把字段标题、单位和输入控件分成彼此独立的行。
 * 工业软件的表单标题位于输入框外，不能与输入框边框叠在一起。
 */
export default function FieldShell({
  label,
  unit,
  hint,
  disabled = false,
  className,
  children,
}: FieldShellProps) {
  return (
    <Box
      className={className ? `field-shell ${className}` : 'field-shell'}
      data-disabled={disabled || undefined}
    >
      <Box className="field-label-row">
        <Typography component="span" className="field-label">
          {label}
        </Typography>
        {unit && (
          <Typography component="span" className="field-unit">
            {unit}
          </Typography>
        )}
      </Box>
      {children}
      {hint && (
        <Typography component="span" className="field-hint">
          {hint}
        </Typography>
      )}
    </Box>
  )
}
