import { beforeEach, describe, expect, it } from 'vitest'

import { restoreTemplateRequest } from '../../src/frontend/features/package-library/requestStorage'
import type { TemplateRequest, TemplateSchema } from '../../src/frontend/features/package-library/types'

const defaults: TemplateRequest = {
  template_id: 'bare_die', design_name: 'Bare Die', overrides: {}, bga: null,
  material_assignments: {}, custom_materials: [], die_power_w: null,
  mesh: { resolution: 'standard' },
}
const schema: TemplateSchema = {
  schema_version: 'packstudio.wizard/v2', template_id: 'bare_die', steps: [], has_bga: false,
  special_rules: { outline_type: 'standard_outline', die_type: 'actual_type',
    bga_pattern: null, flip_chip_bumps: null },
}

beforeEach(() => localStorage.clear())

describe('PACK naming storage boundary', () => {
  it('does not restore an old scheme even when its template name is unchanged', () => {
    localStorage.setItem('packstudio.library.v2.bare_die', JSON.stringify(defaults))
    expect(restoreTemplateRequest('bare_die', defaults, schema)).toBeNull()
  })
})
