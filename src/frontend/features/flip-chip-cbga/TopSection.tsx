import { Box, FormControlLabel, Paper, Switch, Typography } from '@mui/material'

import MaterialFields from './MaterialFields'
import NumberInput from './NumberInput'
import type {
  FlipChipCbgaParameters,
  HeatSlugParameters,
  LidParameters,
} from './types'

interface TopSectionProps {
  parameters: FlipChipCbgaParameters
  onChange: (parameters: FlipChipCbgaParameters) => void
}

export default function TopSection({ parameters, onChange }: TopSectionProps) {
  const updateSlug = (patch: Partial<HeatSlugParameters>) =>
    onChange({ ...parameters, heat_slug: { ...parameters.heat_slug, ...patch } })
  const updateLid = (patch: Partial<LidParameters>) =>
    onChange({ ...parameters, lid: { ...parameters.lid, ...patch } })

  return (
    <Paper variant="outlined" className="parameter-section">
      <Typography variant="h6" component="h3">
        顶盖与嵌入式散热块
      </Typography>
      <FormControlLabel
        control={
          <Switch
            checked={parameters.heat_slug.enabled}
            onChange={(event) => updateSlug({ enabled: event.target.checked })}
          />
        }
        label="包含嵌入式散热块（slug）"
      />
      {parameters.heat_slug.enabled && (
        <Box className="sub-parameter-group">
          <Box className="field-grid field-grid-3">
            <NumberInput
              label="Slug 长度"
              value={parameters.heat_slug.length}
              unit="mm"
              onChange={(length) => updateSlug({ length: length ?? 0 })}
            />
            <NumberInput
              label="Slug 宽度"
              value={parameters.heat_slug.width}
              unit="mm"
              onChange={(width) => updateSlug({ width: width ?? 0 })}
            />
            <NumberInput
              label="Slug 厚度"
              value={parameters.heat_slug.thickness}
              unit="mm"
              onChange={(thickness) => updateSlug({ thickness: thickness ?? 0 })}
            />
            <NumberInput
              label="界面层厚度"
              value={parameters.heat_slug.interface_thickness}
              unit="mm"
              onChange={(interface_thickness) =>
                updateSlug({ interface_thickness: interface_thickness ?? 0 })
              }
            />
          </Box>
          <MaterialFields
            material={parameters.heat_slug.material}
            onChange={(material) => updateSlug({ material })}
          />
          <MaterialFields
            material={parameters.heat_slug.interface_material}
            onChange={(interface_material) => updateSlug({ interface_material })}
          />
        </Box>
      )}
      <FormControlLabel
        control={
          <Switch
            checked={parameters.lid.enabled}
            onChange={(event) => updateLid({ enabled: event.target.checked })}
          />
        }
        label="包含顶盖"
      />
      {parameters.lid.enabled && (
        <Box className="sub-parameter-group">
          <Box className="field-grid field-grid-3">
            <NumberInput
              label="顶盖长度"
              value={parameters.lid.length}
              unit="mm"
              onChange={(length) => updateLid({ length: length ?? 0 })}
            />
            <NumberInput
              label="顶盖宽度"
              value={parameters.lid.width}
              unit="mm"
              onChange={(width) => updateLid({ width: width ?? 0 })}
            />
            <NumberInput
              label="顶盖厚度"
              value={parameters.lid.thickness}
              unit="mm"
              onChange={(thickness) => updateLid({ thickness: thickness ?? 0 })}
            />
            <NumberInput
              label="界面层厚度"
              value={parameters.lid.interface_thickness}
              unit="mm"
              onChange={(interface_thickness) =>
                updateLid({ interface_thickness: interface_thickness ?? 0 })
              }
            />
          </Box>
          <MaterialFields
            material={parameters.lid.material}
            onChange={(material) => updateLid({ material })}
          />
          <MaterialFields
            material={parameters.lid.interface_material}
            onChange={(interface_material) => updateLid({ interface_material })}
          />
        </Box>
      )}
    </Paper>
  )
}
