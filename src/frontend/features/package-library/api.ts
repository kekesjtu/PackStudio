import type {
  Material,
  PackageModel,
  TemplateRequest,
  TemplateSchema,
  TemplateCatalogItem,
} from './types'

const baseUrl = '/api/templates'

export const loadTemplateCatalog = () =>
  getJson<TemplateCatalogItem[]>(baseUrl)

export const loadTemplateSchema = (templateId: string) =>
  getJson<TemplateSchema>(`${baseUrl}/${templateId}/schema`)

export const loadTemplateDefaults = (templateId: string) =>
  getJson<TemplateRequest>(`${baseUrl}/${templateId}/defaults`)

export const loadTemplateMaterials = () =>
  getJson<Material[]>(`${baseUrl}/materials`)

export const generateTemplateModel = (request: TemplateRequest) =>
  postJson<PackageModel>(
    `${baseUrl}/${request.template_id}/generate`,
    request,
  )

export async function downloadTemplatePta(
  request: TemplateRequest,
): Promise<void> {
  const response = await fetch(
    `${baseUrl}/${request.template_id}/export/pta`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    },
  )
  if (!response.ok) throw new Error(await responseError(response))
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${request.template_id.replaceAll('_', '-')}.xml`
  anchor.click()
  URL.revokeObjectURL(url)
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(await responseError(response))
  return (await response.json()) as T
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await responseError(response))
  return (await response.json()) as T
}

async function responseError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown }
    if (typeof payload.detail === 'string') return payload.detail
    if (payload.detail !== undefined) return JSON.stringify(payload.detail)
  } catch {
    // Use the HTTP status below when the response is not JSON.
  }
  return `请求失败：HTTP ${response.status}`
}
