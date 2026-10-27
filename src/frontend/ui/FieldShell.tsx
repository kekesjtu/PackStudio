import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import type { ReactNode } from 'react'

interface FieldShellProps {
  label: string
  unit?: string
  hint?: ReactNode
  sideHint?: ReactNode
  disabled?: boolean
  className?: string
  children: ReactNode
}

/**
 * 字段标题位于输入框外，范围提示与输入控件同排。
 * 工业软件的表单标题位于输入框外，不能与输入框边框叠在一起。
 */
export default function FieldShell({
  label,
  unit,
  hint,
  sideHint,
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
      {sideHint ? (
        <Box className="field-control-row">
          {children}
          <Typography component="span" className="field-hint field-side-hint">
            {sideHint}
          </Typography>
        </Box>
      ) : children}
      {hint && (
        <Typography component="span" className="field-hint">
          {hint}
        </Typography>
      )}
    </Box>
  )
}
