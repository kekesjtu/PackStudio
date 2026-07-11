import { Box, Paper, TextField, Typography } from '@mui/material'

import MaterialFields from './MaterialFields'
import NumberInput from './NumberInput'
import type { FlipChipCbgaParameters } from './types'

interface PackageSectionProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function PackageSection({ parameters, onChange }: PackageSectionProps) {
  const updateSubstrate = (patch: Partial<FlipChipCbgaParameters['substrate']>) => {
    onChange({ ...parameters, substrate: { ...parameters.substrate, ...patch } })
  }
  const updateDie = (patch: Partial<FlipChipCbgaParameters['die']>) => {
    onChange({ ...parameters, die: { ...parameters.die, ...patch } })
  }

  return (
    <Paper variant="outlined" className="parameter-section">
      <Typography variant="h6" component="h3">
        设计、基板与芯片
      </Typography>
      <TextField
        label="设计名称"
        size="small"
        value={parameters.design_name}
        onChange={(event) => onChange({ ...parameters, design_name: event.target.value })}
        fullWidth
      />
      <Typography variant="subtitle1">封装基底</Typography>
      <Box className="field-grid field-grid-3">
        <NumberInput
          label="长度 D"
          value={parameters.substrate.length}
          unit="mm"
          onChange={(value) => updateSubstrate({ length: value ?? 0 })}
        />
        <NumberInput
          label="宽度 E"
          value={parameters.substrate.width}
          unit="mm"
          onChange={(value) => updateSubstrate({ width: value ?? 0 })}
        />
        <NumberInput
          label="厚度 A2"
          value={parameters.substrate.thickness}
          unit="mm"
          onChange={(value) => updateSubstrate({ thickness: value ?? 0 })}
        />
      </Box>
      <MaterialFields
        material={parameters.substrate.material}
        onChange={(material) => updateSubstrate({ material })}
      />
      <Typography variant="subtitle1">芯片与热源</Typography>
      <Box className="field-grid field-grid-3">
        <NumberInput
          label="芯片长度 Ld"
          value={parameters.die.length}
          unit="mm"
          onChange={(value) => updateDie({ length: value ?? 0 })}
        />
        <NumberInput
          label="芯片宽度 Wd"
          value={parameters.die.width}
          unit="mm"
          onChange={(value) => updateDie({ width: value ?? 0 })}
        />
        <NumberInput
          label="芯片厚度 td"
          value={parameters.die.thickness}
          unit="mm"
          onChange={(value) => updateDie({ thickness: value ?? 0 })}
        />
        <NumberInput
          label="封装功率"
          value={parameters.die.power_w}
          unit="W"
          onChange={(value) => updateDie({ power_w: value ?? 0 })}
        />
      </Box>
      <MaterialFields
        material={parameters.die.material}
        onChange={(material) => updateDie({ material })}
      />
    </Paper>
  )
}
