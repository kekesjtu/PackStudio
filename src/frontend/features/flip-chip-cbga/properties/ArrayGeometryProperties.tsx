import { Box, Stack, Typography } from '@mui/material'

import MaterialSelect from '../MaterialSelect'
import NumberInput from '../NumberInput'
import type {
  ArrayLayerParameters,
  FlipChipCbgaParameters,
  Material,
} from '../types'

interface ArrayGeometryPropertiesProps {
  target: 'flip_chip_bumps' | 'solder_balls'
  parameters: FlipChipCbgaParameters
  materials: Material[]
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function ArrayGeometryProperties({
  target,
  parameters,
  materials,
  onChange,
}: ArrayGeometryPropertiesProps) {
  const value = parameters[target]
  const update = (patch: Partial<ArrayLayerParameters>) =>
    onChange({ ...parameters, [target]: { ...value, ...patch } })
  const isBump = target === 'flip_chip_bumps'
  const elementCount = value.rows * value.columns
  const footprintX =
    value.footprint_x_override ?? (value.columns - 1) * value.pitch_x + value.diameter
  const footprintY =
    value.footprint_y_override ?? (value.rows - 1) * value.pitch_y + value.diameter
  const cellDensity = 1 / (value.pitch_x * value.pitch_y)
  const fillFraction =
    (Math.PI * (value.diameter / 2) ** 2) / (value.pitch_x * value.pitch_y)

  return (
    <Stack spacing={2}>
      <Box className="field-grid field-grid-2">
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
          label="直径"
          value={value.diameter}
          unit="mm"
          onChange={(diameter) => update({ diameter: diameter ?? 0 })}
        />
        <NumberInput
          label="层高"
          value={value.height}
          unit="mm"
          onChange={(height) => update({ height: height ?? 0 })}
        />
      </Box>
      {isBump && (
        <>
          <Box className="array-metrics">
            <Typography variant="body2">凸点数量：{elementCount}</Typography>
            <Typography variant="body2">
              阵列包络：{footprintX.toFixed(3)} × {footprintY.toFixed(3)} mm
            </Typography>
            <Typography variant="body2">
              单元密度：{Number.isFinite(cellDensity) ? cellDensity.toFixed(2) : '—'} 个/mm²
            </Typography>
            <Typography variant="body2">
              截面填充率：{Number.isFinite(fillFraction) ? (fillFraction * 100).toFixed(2) : '—'}%
            </Typography>
          </Box>
          <Typography variant="body2">建模方式：正交各向异性等效层</Typography>
        </>
      )}
      <MaterialSelect
        label={isBump ? '凸点材料' : '焊球材料'}
        value={value.element_material}
        materials={materials}
        onChange={(element_material) => update({ element_material })}
      />
      {isBump ? (
        <MaterialSelect
          label="Underfill 材料"
          value={value.matrix_material}
          materials={materials}
          onChange={(matrix_material) => update({ matrix_material })}
        />
      ) : (
        <Typography variant="body2">焊球单元间隙与去球区域固定填充静态空气。</Typography>
      )}
    </Stack>
  )
}
