import type { FlipChipCbgaParameters, PackageModel } from './types'

const templateUrl = '/api/templates/flip-chip-cbga'

export async function generateModel(
  parameters: FlipChipCbgaParameters,
): Promise<PackageModel> {
  return requestJson<PackageModel>(`${templateUrl}/generate`, parameters)
}

export async function downloadPtaXml(parameters: FlipChipCbgaParameters): Promise<void> {
  const response = await fetch(`${templateUrl}/export/pta`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parameters),
  })
  if (!response.ok) {
    throw new Error(await responseError(response))
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'flip-chip-cbga.xml'
  anchor.click()
  URL.revokeObjectURL(url)
}

async function requestJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(await responseError(response))
  }
  return (await response.json()) as T
}

async function responseError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown }
    if (typeof payload.detail === 'string') {
      return payload.detail
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => (typeof item === 'object' ? JSON.stringify(item) : String(item)))
        .join('; ')
    }
  } catch {
    // Fall through to the status message when the server did not return JSON.
  }
  return `请求失败：HTTP ${response.status}`
}
