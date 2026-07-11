import { Box, Button, CircularProgress, Divider, Stack, Typography } from '@mui/material'

import { propertySection, type PropertySectionId } from './propertySections'
import ArrayGeometryProperties from './properties/ArrayGeometryProperties'
import BasicStructureProperties from './properties/BasicStructureProperties'
import CenterSolderProperties from './properties/CenterSolderProperties'
import EncapsulantProperties from './properties/EncapsulantProperties'
import ModelingOptionsProperties from './properties/ModelingOptionsProperties'
import SolderRemovalProperties from './properties/SolderRemovalProperties'
import SummaryProperties from './properties/SummaryProperties'
import TopStructureProperties from './properties/TopStructureProperties'
import type { FlipChipCbgaParameters, Material, PackageModel } from './types'

interface PropertyPanelProps {
  activeSection: PropertySectionId
  parameters: FlipChipCbgaParameters
  materials: Material[]
  model: PackageModel | null
  onChange: (parameters: FlipChipCbgaParameters) => void
  onGenerate: () => void
  onExport: () => void
  busy: boolean
}

export default function PropertyPanel(props: PropertyPanelProps) {
  const section = propertySection(props.activeSection)
  return (
    <Box className="property-editor">
      <Box>
        <Typography variant="h5" component="h2">
          {section.label}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {section.description}
        </Typography>
      </Box>
      <Divider />
      <Box className="property-content">{renderProperties(props)}</Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} className="action-bar">
        <Button variant="contained" onClick={props.onGenerate} disabled={props.busy}>
          {props.busy ? <CircularProgress size={21} color="inherit" /> : '生成模型'}
        </Button>
        <Button variant="outlined" onClick={props.onExport} disabled={props.busy || !props.model}>
          导出精简 PTA XML
        </Button>
      </Stack>
    </Box>
  )
}

function renderProperties(props: PropertyPanelProps) {
  const shared = {
    parameters: props.parameters,
    materials: props.materials,
    onChange: props.onChange,
  }
  switch (props.activeSection) {
    case 'summary':
      return <SummaryProperties {...shared} model={props.model} />
    case 'substrate':
      return <BasicStructureProperties {...shared} target="substrate" />
    case 'die':
      return <BasicStructureProperties {...shared} target="die" />
    case 'encapsulant':
      return <EncapsulantProperties {...shared} />
    case 'flip_chip_bumps':
      return <ArrayGeometryProperties {...shared} target="flip_chip_bumps" />
    case 'solder_balls':
      return <ArrayGeometryProperties {...shared} target="solder_balls" />
    case 'solder_removal':
      return <SolderRemovalProperties {...shared} />
    case 'center_solder':
      return <CenterSolderProperties {...shared} />
    case 'lid':
      return <TopStructureProperties {...shared} target="lid" />
    case 'heat_slug':
      return <TopStructureProperties {...shared} target="heat_slug" />
    case 'modeling_options':
      return <ModelingOptionsProperties {...shared} />
  }
}
