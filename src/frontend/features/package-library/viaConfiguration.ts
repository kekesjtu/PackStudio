import type { TemplateRequest, WizardField } from './types'
import { valueFor } from './wizardValues'

export function viaDimensions(fields: WizardField[], request: TemplateRequest) {
  // Chip Array places one via at each solder-array cell.
  const prefix = fields.some((field) => field.property_name === 'vias.rows') ? 'vias' : 'bga'
  const read = (axis: string) => {
    const field = fields.find((item) => item.property_name === `${prefix}.${axis}`)
    const input = field ? valueFor(field, request, fields) : null
    const value = typeof input === 'number' ? input : 0
    return Number.isFinite(value) ? Math.max(0, Math.min(50, Math.trunc(value))) : 0
  }
  return { rows: read('rows'), columns: read('columns') }
}

export function pruneViaConfiguration(request: TemplateRequest, fields: WizardField[]): TemplateRequest {
  if (!request.vias) return request
  const { rows, columns } = viaDimensions(fields, request)
  const regionRows = request.vias.removal_rows === null ? null
    : Math.max(0, Math.min(rows, request.vias.removal_rows))
  const regionColumns = request.vias.removal_columns === null ? null
    : Math.max(0, Math.min(columns, request.vias.removal_columns))
  return { ...request, vias: {
    ...request.vias,
    removal_rows: regionRows,
    removal_columns: regionColumns,
    omitted_cells: request.vias.omitted_cells.filter((cell) =>
      cell.row >= 0 && cell.row < rows && cell.column >= 0 && cell.column < columns),
  } }
}
