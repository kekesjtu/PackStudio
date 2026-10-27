import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'

import FieldShell from '../../ui/FieldShell'
import type { BgaConfiguration, TemplateRequest } from './types'

type Representation = BgaConfiguration['representation']
const labels: Record<Representation, string> = {
  equivalent: 'Orthotropic Cuboid', discrete: 'Discrete Cuboids', isotropic: 'Isotropic Cuboid',
}

export default function ModelingFields({ request, onChange }: {
  request: TemplateRequest
  onChange: (value: TemplateRequest) => void
}) {
  const choices: Representation[] = request.template_id === 'chip_array' ? ['discrete']
    : request.template_id === 'pbga_wb' ? ['isotropic', 'discrete', 'equivalent']
    : ['equivalent', 'discrete']
  const bumpLabel = request.template_id === 'bare_die' ? 'Solder Bump Modeling' : 'Model Flip Chip Bumps As'
  const hasBumps = ['bare_die', 'cbga_fc', 'pbga_fc'].includes(request.template_id)
  return <Stack spacing={1.5}>
    {request.bga && <FieldShell label="Model Solder Ball Array As">
      <TextField select size="small" value={request.bga.representation}
        slotProps={{ select: { native: true, inputProps: { 'aria-label': 'Model Solder Ball Array As' } } }}
        onChange={(event) => onChange({ ...request,
          bga: { ...request.bga!, representation: event.target.value as Representation } })}>
        {choices.map((choice) => <option key={choice} value={choice}
          disabled={choice !== 'discrete' && (request.bga!.ball_map_enabled || request.bga!.omitted_cells.length > 0)}>
          {labels[choice]}
        </option>)}
      </TextField>
    </FieldShell>}
    {hasBumps && <FieldShell label={bumpLabel}>
      <TextField select size="small" defaultValue="isotropicCuboid"
        slotProps={{ select: { native: true, inputProps: { 'aria-label': bumpLabel } } }}>
        <option value="isotropicCuboid">Isotropic Cuboid</option>
      </TextField>
    </FieldShell>}
  </Stack>
}
