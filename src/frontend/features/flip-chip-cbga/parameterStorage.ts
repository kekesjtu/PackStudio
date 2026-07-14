import type { FlipChipCbgaParameters } from './types'

const storageKey = 'packstudio.flip-chip-cbga.parameters.v1'
const schemaVersion = 'packstudio.parameters/v1'

interface StoredParameters {
  schema_version: typeof schemaVersion
  template_id: 'flip-chip-cbga'
  parameters: FlipChipCbgaParameters
}

export function loadSavedParameters(): FlipChipCbgaParameters | null {
  try {
    const raw = window.localStorage.getItem(storageKey)
    if (raw === null) return null
    const payload: unknown = JSON.parse(raw)
    return isStoredParameters(payload) ? payload.parameters : null
  } catch {
    return null
  }
}

export function saveParameters(parameters: FlipChipCbgaParameters): void {
  const payload: StoredParameters = {
    schema_version: schemaVersion,
    template_id: 'flip-chip-cbga',
    parameters,
  }
  window.localStorage.setItem(storageKey, JSON.stringify(payload))
}

function isStoredParameters(value: unknown): value is StoredParameters {
  if (!isRecord(value) || value.schema_version !== schemaVersion) return false
  if (value.template_id !== 'flip-chip-cbga' || !isRecord(value.parameters)) return false
  const parameters = value.parameters
  if (typeof parameters.design_name !== 'string' || !isRecord(parameters.substrate)) return false
  if (!isRecord(parameters.solder_balls) || !isRecord(parameters.flip_chip_bumps)) return false
  return (
    typeof parameters.solder_balls.center_solder_enabled === 'boolean' &&
    typeof parameters.solder_balls.solder_removal_enabled === 'boolean' &&
    parameters.flip_chip_bumps.representation === 'equivalent'
  )
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
