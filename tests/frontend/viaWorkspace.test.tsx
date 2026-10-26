import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'

import * as api from '../../src/frontend/features/package-library/api'
import PackageWorkspace from '../../src/frontend/features/package-library/PackageWorkspace'
import type { TemplateSchema, WizardField } from '../../src/frontend/features/package-library/types'
import { model, request } from './materialQualityFixtures'

vi.mock('../../src/frontend/features/package-library/api')
vi.mock('../../src/frontend/features/model-editor/ModelPreview', () => ({ default: () => null }))

const defaults = { ...request, template_id: 'qfn', vias: {
  removal_enabled: false, removal_rows: 0, removal_columns: 0, omitted_cells: [],
} }
const fields = [
  ['vias.enabled', false, 'checkbox', '启用热通孔'],
  ['vias.rows', 3, 'integer_spinbox', '通孔行数'],
  ['vias.columns', 4, 'integer_spinbox', '通孔列数'],
].map(([property, initial, control, label]) => ({
  target_id: `qfn.${property}`, property_name: property, label,
  default: initial, control, ui_location: 'thermal_vias', component: null,
  options: [], supported_values: [], classification: 'numeric_parameter',
  evidence_status: 'implemented', editable: true,
})) as WizardField[]
const schema: TemplateSchema = {
  template_id: 'qfn', schema_version: 'packstudio.wizard/v2', has_bga: false,
  steps: [{ id: 'thermal_vias', label: '热通孔', fields }],
  special_rules: { outline_type: 'standard_outline', die_type: 'actual_type', bga_pattern: null, flip_chip_bumps: null },
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(api.loadTemplateSchema).mockResolvedValue(schema)
  vi.mocked(api.loadTemplateDefaults).mockResolvedValue(defaults)
  vi.mocked(api.loadTemplateMaterials).mockResolvedValue([])
  vi.mocked(api.generateTemplateModel).mockResolvedValue(model)
})

it('passes via enablement and matrix edits through workspace generation', async () => {
  render(<PackageWorkspace templateId="qfn" />)
  await screen.findByText('1 个块')
  expect(screen.queryByRole('button', { name: '建模选项' })).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: '热通孔' }))
  fireEvent.click(screen.getByRole('switch', { name: '启用热通孔' }))
  fireEvent.click(screen.getByRole('button', { name: '热通孔去除' }))
  fireEvent.click(screen.getByRole('switch', { name: '热通孔去除' }))
  fireEvent.click(screen.getByRole('button', { name: '行 2，列 3，添加显式去孔' }))
  fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
  await waitFor(() => expect(api.generateTemplateModel).toHaveBeenCalledTimes(2))
  expect(api.generateTemplateModel).toHaveBeenLastCalledWith({
    ...defaults, overrides: { 'qfn.vias.enabled': true },
    vias: { ...defaults.vias, removal_enabled: true, omitted_cells: [{ row: 2, column: 3 }] },
  })
})
