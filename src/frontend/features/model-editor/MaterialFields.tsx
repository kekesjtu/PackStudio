import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

import NumberInput from './NumberInput'
import type { Material } from './types'

interface MaterialFieldsProps {
  material: Material
  onChange: (material: Material) => void
  showTitle?: boolean
}

export default function MaterialFields({
  material,
  onChange,
  showTitle = true,
}: MaterialFieldsProps) {
  const updateConductivity = (axis: 'x' | 'y' | 'z', value: number | null) => {
    onChange({
      ...material,
      conductivity: { ...material.conductivity, [axis]: value ?? 0 },
    })
  }

  return (
    <Box className="material-fields">
      {showTitle && <Typography variant="subtitle2">{material.name}</Typography>}
      <Box className="field-grid field-grid-3">
        <NumberInput
          label="kx"
          value={material.conductivity.x}
          unit="W/(m·K)"
          onChange={(value) => updateConductivity('x', value)}
        />
        <NumberInput
          label="ky"
          value={material.conductivity.y}
          unit="W/(m·K)"
          onChange={(value) => updateConductivity('y', value)}
        />
        <NumberInput
          label="kz"
          value={material.conductivity.z}
          unit="W/(m·K)"
          onChange={(value) => updateConductivity('z', value)}
        />
        <NumberInput
          label="密度"
          value={material.density}
          unit="kg/m³"
          onChange={(value) => onChange({ ...material, density: value ?? 0 })}
        />
        <NumberInput
          label="比热"
          value={material.specific_heat}
          unit="J/(kg·K)"
          onChange={(value) => onChange({ ...material, specific_heat: value ?? 0 })}
        />
      </Box>
    </Box>
  )
}
