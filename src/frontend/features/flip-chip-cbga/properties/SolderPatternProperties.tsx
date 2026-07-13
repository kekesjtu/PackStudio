import { useState } from 'react'
import { Box, FormControl, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material'

import NumberInput from '../NumberInput'
import type {
  ArrayLayerParameters,
  ArrayPattern,
  CellIndex,
  FlipChipCbgaParameters,
} from '../types'

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
  const update = (patch: Partial<ArrayLayerParameters>) =>
    onChange({ ...parameters, solder_balls: { ...value, ...patch } })
  const centerPattern =
    value.pattern === 'center_depopulated' || value.pattern === 'center_populated'

  const changePattern = (pattern: ArrayPattern) => {
    const patch: Partial<ArrayLayerParameters> = { pattern }
    const nextCenterPattern = pattern === 'center_depopulated' || pattern === 'center_populated'
    if (nextCenterPattern) {
      patch.center_rows = value.center_rows || defaultCenterSize(value.rows)
      patch.center_columns = value.center_columns || defaultCenterSize(value.columns)
    } else {
      patch.center_rows = 0
      patch.center_columns = 0
    }
    if (pattern !== 'custom') patch.omitted_cells = []
    update(patch)
  }

  return (
    <Stack spacing={2}>
      <FormControl size="small" fullWidth>
        <InputLabel>焊球样式</InputLabel>
        <Select
          label="焊球样式"
          value={value.pattern}
          onChange={(event) => changePattern(event.target.value as ArrayPattern)}
        >
          <MenuItem value="full">全阵列（默认）</MenuItem>
          <MenuItem value="staggered">交错阵列</MenuItem>
          <MenuItem value="center_depopulated">中央去球</MenuItem>
          <MenuItem value="center_populated">中央焊球分区</MenuItem>
          <MenuItem value="custom">自定义去球</MenuItem>
        </Select>
      </FormControl>
      {centerPattern && (
        <Box className="field-grid field-grid-2">
          <NumberInput
            label="中央区域行数"
            value={value.center_rows}
            integer
            onChange={(center_rows) => update({ center_rows: center_rows ?? 0 })}
          />
          <NumberInput
            label="中央区域列数"
            value={value.center_columns}
            integer
            onChange={(center_columns) => update({ center_columns: center_columns ?? 0 })}
          />
        </Box>
      )}
      {value.pattern === 'custom' && (
        <TextField
          label="去除单元（1 基行,列）"
          size="small"
          value={omittedText}
          onChange={(event) => setOmittedText(event.target.value)}
          onBlur={() => update({ omitted_cells: parseOmittedCells(omittedText) })}
          helperText="示例：2,2; 2,3; 3,2; 3,3"
          fullWidth
        />
      )}
    </Stack>
  )
}

const defaultCenterSize = (total: number) =>
  total < 3 ? 0 : total % 2 === 0 ? 2 : Math.min(3, total - 2)

const formatOmittedCells = (cells: CellIndex[]) =>
  cells.map((cell) => `${cell.row + 1},${cell.column + 1}`).join('; ')

const parseOmittedCells = (value: string): CellIndex[] =>
  value
    .split(';')
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => token.split(',').map((part) => Number.parseInt(part.trim(), 10)))
    .filter(([row, column]) => Number.isInteger(row) && Number.isInteger(column))
    .map(([row, column]) => ({ row: row - 1, column: column - 1 }))
