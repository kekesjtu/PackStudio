import { useState } from 'react'
import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
} from '@mui/material'

import MaterialFields from './MaterialFields'
import NumberInput from './NumberInput'
import type {
  ArrayLayerParameters,
  ArrayPattern,
  ArrayRepresentation,
  CellIndex,
  VoidFillMode,
} from './types'

interface ArraySectionProps {
  title: string
  description: string
  value: ArrayLayerParameters
  onChange: (value: ArrayLayerParameters) => void
}

const centerPatterns: ArrayPattern[] = ['center_depopulated', 'center_populated']

export default function ArraySection({
  title,
  description,
  value,
  onChange,
}: ArraySectionProps) {
  const [omittedText, setOmittedText] = useState(formatOmittedCells(value.omitted_cells))
  const update = (patch: Partial<ArrayLayerParameters>) => onChange({ ...value, ...patch })

  const changePattern = (pattern: ArrayPattern) => {
    const patch: Partial<ArrayLayerParameters> = { pattern }
    if (centerPatterns.includes(pattern) && (!value.center_rows || !value.center_columns)) {
      patch.center_rows = value.rows % 2 === 0 ? 2 : Math.min(3, value.rows - 2)
      patch.center_columns = value.columns % 2 === 0 ? 2 : Math.min(3, value.columns - 2)
    }
    if (pattern !== 'custom') {
      patch.omitted_cells = []
    }
    update(patch)
  }

  return (
    <Paper variant="outlined" className="parameter-section">
      <Box>
        <Typography variant="h6" component="h3">
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>
      <Box className="field-grid field-grid-3">
        <NumberInput
          label="行数"
          value={value.rows}
          integer
          onChange={(rows) => update({ rows: rows ?? 0 })}
        />
        <NumberInput
          label="列数"
          value={value.columns}
          integer
          onChange={(columns) => update({ columns: columns ?? 0 })}
        />
        <NumberInput
          label="直径"
          value={value.diameter}
          unit="mm"
          onChange={(diameter) => update({ diameter: diameter ?? 0 })}
        />
        <NumberInput
          label="X pitch"
          value={value.pitch_x}
          unit="mm"
          onChange={(pitch_x) => update({ pitch_x: pitch_x ?? 0 })}
        />
        <NumberInput
          label="Y pitch"
          value={value.pitch_y}
          unit="mm"
          onChange={(pitch_y) => update({ pitch_y: pitch_y ?? 0 })}
        />
        <NumberInput
          label="层高"
          value={value.height}
          unit="mm"
          onChange={(height) => update({ height: height ?? 0 })}
        />
        <FormControl size="small" fullWidth>
          <InputLabel>阵列模式</InputLabel>
          <Select
            label="阵列模式"
            value={value.pattern}
            onChange={(event) => changePattern(event.target.value as ArrayPattern)}
          >
            <MenuItem value="full">全阵列</MenuItem>
            <MenuItem value="staggered">交错阵列</MenuItem>
            <MenuItem value="center_depopulated">中央去球</MenuItem>
            <MenuItem value="center_populated">中央焊球</MenuItem>
            <MenuItem value="custom">自定义去球</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" fullWidth>
          <InputLabel>建模方式</InputLabel>
          <Select
            label="建模方式"
            value={value.representation}
            onChange={(event) =>
              update({ representation: event.target.value as ArrayRepresentation })
            }
          >
            <MenuItem value="equivalent">各向异性等效块</MenuItem>
            <MenuItem value="discrete">离散等体积方柱</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" fullWidth>
          <InputLabel>空缺区域</InputLabel>
          <Select
            label="空缺区域"
            value={value.void_fill}
            onChange={(event) => update({ void_fill: event.target.value as VoidFillMode })}
          >
            <MenuItem value="matrix">填充基体材料</MenuItem>
            <MenuItem value="omit">不建模</MenuItem>
          </Select>
        </FormControl>
      </Box>
      {centerPatterns.includes(value.pattern) && (
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
      <FormControlLabel
        control={
          <Checkbox
            checked={value.emit_matrix_blocks}
            onChange={(event) => update({ emit_matrix_blocks: event.target.checked })}
          />
        }
        label="离散模式生成焊点周围基体矩形块"
      />
      <MaterialFields
        material={value.element_material}
        onChange={(element_material) => update({ element_material })}
      />
      <MaterialFields
        material={value.matrix_material}
        onChange={(matrix_material) => update({ matrix_material })}
      />
    </Paper>
  )
}

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
