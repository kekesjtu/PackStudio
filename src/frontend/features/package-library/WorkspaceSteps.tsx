import Stack from '@mui/material/Stack'

import BgaConfigurationPanel from './BgaConfigurationPanel'
import NativeBgaPanel from './NativeBgaPanel'
import SolderBallMap from './SolderBallMap'
import SopNominalPaths from './SopNominalPaths'
import ViaRemovalPanel from './ViaRemovalPanel'
import WizardFields from './WizardFields'
import { SummaryFields } from './WorkspaceSpecialFields'
import ModelingFields from './ModelingFields'
import type { Material, TemplateRequest, TemplateSchema, WizardField } from './types'
import { valueFor } from './wizardValues'
import { viaDimensions } from './viaConfiguration'

export function renderStep(
  schema: TemplateSchema,
  activeStep: string,
  allFields: TemplateSchema['steps'][number]['fields'],
  request: TemplateRequest,
  materials: Material[],
  onChange: (request: TemplateRequest) => void,
) {
  const nativeBalls = ['chip_array', 'cbga_fc', 'pbga_fc', 'pbga_wb'].includes(request.template_id)
  const BallPanel = nativeBalls ? NativeBgaPanel : BgaConfigurationPanel
  if (activeStep === 'packstudio_summary') {
    return <SummaryFields request={request} onChange={onChange} />
  }
  const { rows: arrayRows, columns: arrayColumns } = arrayDimensions(allFields, request, 'bga')
  if (activeStep === 'packstudio_via_removal' && request.vias) {
    const dimensions = viaDimensions(allFields, request)
    const enabled = allFields.find((field) => field.property_name === 'vias.enabled')
    return <ViaRemovalPanel value={request.vias} {...dimensions}
      enabled={enabled ? Boolean(valueFor(enabled, request, allFields)) : false}
      onChange={(vias) => onChange({ ...request, vias })} />
  }
  if (activeStep === 'packstudio_bga_removal' && request.bga) {
    return (
      <BallPanel
        section="removal"
        value={request.bga}
        rows={arrayRows}
        columns={arrayColumns}
        onChange={(bga) => onChange({ ...request, bga })}
      />
    )
  }
  if (activeStep === 'packstudio_bga_center' && request.bga) {
    return (
      <BallPanel
        section="center"
        value={request.bga}
        rows={arrayRows}
        columns={arrayColumns}
        onChange={(bga) => onChange({ ...request, bga })}
      />
    )
  }
  if (activeStep === 'packstudio_modeling' || activeStep === 'modeling') {
    const modeling = schema.steps.find((step) => step.id === 'modeling')
    const gridFields = modeling?.fields.filter((field) => field.property_name?.startsWith('grid.')) ?? []
    const modelFields = modeling?.fields.filter((field) => !field.property_name?.startsWith('grid.')) ?? []
    return <Stack spacing={2}>
      <ModelingFields request={request} onChange={onChange} />
      {modeling && modelFields.length > 0 && <WizardFields step={{ ...modeling, fields: modelFields }} allFields={allFields}
        request={request} materials={materials} onChange={onChange} />}
      {modeling && gridFields.length > 0 && <WizardFields step={{ ...modeling, fields: gridFields }} allFields={allFields}
        request={request} materials={materials} onChange={onChange} />}
    </Stack>
  }
  const step = schema.steps.find((item) => item.id === activeStep) ?? schema.steps[0]
  return <>
    <WizardFields step={step} allFields={allFields} request={request} materials={materials} onChange={onChange} />
    {request.template_id === 'sop' && activeStep === 'bond_wires'
      && <SopNominalPaths request={request} fields={allFields} />}
    {nativeBalls && activeStep === 'solder_balls' && request.bga && <SolderBallMap
      key={request.template_id + String(request.overrides[`${request.template_id}.footprint.size`])}
      value={request.bga} onChange={(bga) => onChange({ ...request, bga })} />}
  </>
}

export function stepTitle(schema: TemplateSchema, stepId: string) {
  if (stepId === 'packstudio_summary') return '概要'
  if (stepId === 'packstudio_bga_removal') return '焊球去除'
  if (stepId === 'packstudio_bga_center') return '中央焊球'
  if (stepId === 'packstudio_via_removal') return '热通孔去除'
  if (stepId === 'packstudio_modeling' || stepId === 'modeling') return '建模选项'
  return schema.steps.find((step) => step.id === stepId)?.label ?? '参数'
}

function arrayDimensions(fields: WizardField[], request: TemplateRequest, prefix: string) {
  const readDimension = (propertyName: string) => {
    const field = fields.find((candidate) => candidate.property_name === propertyName)
    if (!field) return 1
    const value = Number(valueFor(field, request, fields))
    return Number.isFinite(value) ? Math.max(1, Math.min(50, Math.trunc(value))) : 1
  }
  return { rows: readDimension(`${prefix}.rows`), columns: readDimension(`${prefix}.columns`) }
}
