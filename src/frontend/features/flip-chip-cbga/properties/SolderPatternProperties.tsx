import { useState } from 'react'
import { Box, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material'

import NumberInput from '../NumberInput'
import type { CellIndex, FlipChipCbgaParameters, SolderBallParameters } from '../types'

interface SolderPatternPropertiesProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function SolderPatternProperties({
  parameters,
  onChange,
}: SolderPatternPropertiesProps) {
  const value = parameters.solder_balls
  const [omittedText, setOmittedText] = useState(formatOmittedCells(value.omitted_cells))
  const update = (patch: Partial<SolderBallParameters>) =>
    onChange({ ...parameters, solder_balls: { ...value, ...patch } })

  const toggleCenterSolder = (enabled: boolean) => {
    const rows = validCenterSize(value.center_solder_rows, value.rows)
      ? value.center_solder_rows
      : defaultCenterSolderSize(value.rows)
    const columns = validCenterSize(value.center_solder_columns, value.columns)
      ? value.center_solder_columns
      : defaultCenterSolderSize(value.columns)
    update({
      center_solder_enabled: enabled,
      center_solder_rows: rows,
      center_solder_columns: columns,
    })
  }

  const toggleRemoval = (enabled: boolean) => {
    const rows = validCenterSize(value.removal_rows, value.rows)
      ? value.removal_rows
      : defaultRemovalSize(value.rows)
    const columns = validCenterSize(value.removal_columns, value.columns)
      ? value.removal_columns
      : defaultRemovalSize(value.columns)
    update({
      solder_removal_enabled: enabled,
      removal_rows: rows,
      removal_columns: columns,
      omitted_cells: enabled ? value.omitted_cells : [],
    })
  }

  return (
    <Stack spacing={2}>
      <FormControlLabel
        control={
          <Checkbox
            checked={value.center_solder_enabled}
            onChange={(event) => toggleCenterSolder(event.target.checked)}
          />
        }
        label="中央焊球"
      />
      {value.center_solder_enabled && (
        <Box className="field-grid field-grid-2">
          <NumberInput
            label="中央焊球行数"
            value={value.center_solder_rows}
            integer
            onChange={(center_solder_rows) =>
              update({ center_solder_rows: center_solder_rows ?? 1 })
            }
          />
          <NumberInput
            label="中央焊球列数"
            value={value.center_solder_columns}
            integer
            onChange={(center_solder_columns) =>
              update({ center_solder_columns: center_solder_columns ?? 1 })
            }
          />
        </Box>
      )}

      <FormControlLabel
        control={
          <Checkbox
            checked={value.solder_removal_enabled}
            onChange={(event) => toggleRemoval(event.target.checked)}
          />
        }
        label="焊球去除"
      />
      {value.solder_removal_enabled && (
        <Stack spacing={2}>
          <Box className="field-grid field-grid-2">
            <NumberInput
              label="中央去球区行数"
              value={value.removal_rows}
              integer
              onChange={(removal_rows) => update({ removal_rows: removal_rows ?? 1 })}
            />
            <NumberInput
              label="中央去球区列数"
              value={value.removal_columns}
              integer
              onChange={(removal_columns) => update({ removal_columns: removal_columns ?? 1 })}
            />
          </Box>
          <TextField
            label="附加去除单元（1 基行,列）"
            size="small"
            value={omittedText}
            onChange={(event) => setOmittedText(event.target.value)}
            onBlur={() => update({ omitted_cells: parseOmittedCells(omittedText) })}
            helperText="示例：2,2; 2,3；显式去除优先于中央焊球"
            fullWidth
          />
        </Stack>
      )}
      {value.center_solder_enabled && value.solder_removal_enabled && (
        <Typography variant="body2" color="text.secondary">
          中央焊球会在中央去球区内重新加入；两者尺寸差形成静态空气间隔。
        </Typography>
      )}
    </Stack>
  )
}

const validCenterSize = (size: number, total: number) =>
  size > 0 && size < total && (total - size) % 2 === 0

const defaultRemovalSize = (total: number) => Math.max(1, total - 2)

const defaultCenterSolderSize = (total: number) => Math.max(1, total - 4)

const formatOmittedCells = (cells: CellIndex[]) =>
  cells.map((cell) => `${cell.row + 1},${cell.column + 1}`).join('; ')

const parseOmittedCells = (value: string): CellIndex[] =>
  value
    .split(';')
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => token.split(',').map((part) => Number.parseInt(part.trim(), 10)))
    .filter(([row, column]) => Number.isInteger(row) && Number.isInteger(column) && row > 0 && column > 0)
    .map(([row, column]) => ({ row: row - 1, column: column - 1 }))
