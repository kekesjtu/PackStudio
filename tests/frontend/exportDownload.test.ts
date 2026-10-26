import { afterEach, describe, expect, it, vi } from 'vitest'

import { downloadTemplateModel } from '../../src/frontend/features/package-library/api'
import type { TemplateRequest } from '../../src/frontend/features/package-library/types'

const request = { template_id: 'bare_die', design_name: '设计' } as TemplateRequest

afterEach(() => vi.restoreAllMocks())

describe('FloXML model downloads', () => {
  it('downloads FloXML with its route and filename', async () => {
    const anchor = document.createElement('a')
    const createElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag, options) =>
      tag === 'a' ? anchor : createElement(tag, options),
    )
    const click = vi.spyOn(anchor, 'click').mockImplementation(() => undefined)
    const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      { ok: true, blob: async () => new Blob(['<xml_case/>']) } as Response,
    )
    const createUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    const revokeUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)

    await downloadTemplateModel(request)

    expect(fetch).toHaveBeenCalledWith('/api/templates/bare_die/export/floxml', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
    })
    expect(anchor.download).toBe('bare_die.floxml')
    expect(click).toHaveBeenCalledOnce()
    expect(createUrl).toHaveBeenCalledOnce()
    expect(revokeUrl).toHaveBeenCalledWith('blob:test')
  })

  it('surfaces validation errors without starting a download', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      { ok: false, json: async () => ({ detail: '无效尺寸' }) } as Response,
    )
    const createUrl = vi.spyOn(URL, 'createObjectURL')
    await expect(downloadTemplateModel(request)).rejects.toThrow('无效尺寸')
    expect(createUrl).not.toHaveBeenCalled()
  })
})
