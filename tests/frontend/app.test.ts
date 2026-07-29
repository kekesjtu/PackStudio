import { createElement } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../../src/frontend/App'
import type {
  PackageModel,
  TemplateRequest,
  TemplateSchema,
  TemplateCatalogItem,
} from '../../src/frontend/features/package-library/types'

vi.mock('../../src/frontend/features/flip-chip-cbga/ModelPreview', () => ({
  default: () => createElement('div', { 'aria-label': '测试三维模型' }),
}))

const catalog: TemplateCatalogItem[] = [
  template('flip_chip_cbga', 'Flip Chip CBGA', true),
  template('bare_die', 'Bare Die', false),
]

const schema: TemplateSchema = {
  schema_version: 'packstudio.wizard/v2',
  template_id: 'flip_chip_cbga',
  has_bga: true,
  special_rules: {
    bga_pattern: 'implicit_full_with_center_and_removal',
    flip_chip_bumps: 'thick_orthotropic_equivalent',
  },
  steps: [
    {
      id: 'die',
      label: 'Die',
      fields: [
        {
          target_id: 'flip_chip_cbga.cover.type',
          ui_location: 'die',
          component: 'package',
          label: '顶部结构',
          control: 'select',
          default: 'bare_die',
          options: ['bare_die', 'lid'],
          classification: 'enum_option',
          property_name: 'cover.type',
          supported_values: ['bare_die', 'lid'],
          evidence_status: 'implemented',
          editable: true,
        },
        {
          target_id: 'flip_chip_cbga.lid.thickness',
          ui_location: 'die',
          component: 'package',
          label: '顶盖厚度',
          control: 'number',
          default: 0.3,
          options: [],
          classification: 'numeric_parameter',
          property_name: 'lid.thickness',
          supported_values: [0.05, 3],
          evidence_status: 'implemented',
          editable: true,
          visible_when: { 'cover.type': 'lid' },
        },
        {
          target_id: 'flip_chip_cbga.die.length',
          ui_location: 'die',
          component: 'die',
          label: 'Die Length Ld',
          control: 'number',
          default: 1.8,
          options: [],
          classification: 'numeric_parameter',
          property_name: 'dieLengthLd',
          supported_values: [1.62, 1.8, 1.98],
          evidence_status: 'implemented',
          editable: true,
        },
      ],
    },
  ],
}

const defaults: TemplateRequest = {
  template_id: 'flip_chip_cbga',
  design_name: 'Flip Chip CBGA',
  overrides: {},
  bga: {
    representation: 'equivalent',
    center_solder_enabled: false,
    center_solder_rows: 1,
    center_solder_columns: 1,
    solder_removal_enabled: false,
    removal_rows: 3,
    removal_columns: 3,
    omitted_cells: [],
  },
  material_assignments: {},
  custom_materials: [],
  die_power_w: null,
  mesh: { resolution: 'standard' },
  environment: {
    ambient_temperature_k: 300,
    default_convection_coefficient_w_m2k: 10,
    pcb_convection_coefficient_w_m2k: 1600,
    top_convection_coefficient_w_m2k: 10,
  },
}

const generatedModel: PackageModel = {
  schema_version: 'packstudio.model/v1',
  template_id: 'flip-chip-cbga',
  name: 'Flip Chip CBGA',
  length_unit: 'mm',
  coordinate_system: {
    origin: 'substrate bottom-face center',
    x_axis: 'package length',
    y_axis: 'package width',
    z_axis: 'upward through package thickness',
  },
  materials: [
    {
      id: 'alumina',
      name: 'Alumina',
      conductivity: { x: 16, y: 16, z: 16 },
      density: 3970,
      specific_heat: 765,
      color: '#6975DC',
    },
  ],
  blocks: [
    {
      id: 'substrate',
      name: 'Package substrate',
      structure_type: 'substrate',
      origin: { x: -3, y: -3, z: 0 },
      size: { x: 6, y: 6, z: 1.15 },
      material_id: 'alumina',
      parent_group_id: 'group-substrate',
      metadata: {},
    },
  ],
  groups: [
    { id: 'package', name: 'Flip Chip CBGA', parent_id: null, block_ids: [] },
    {
      id: 'group-substrate',
      name: 'Substrate',
      parent_id: 'package',
      block_ids: ['substrate'],
    },
  ],
  heat_sources: [],
  boundaries: [],
  metadata: { solder_ball_footprint_x_mm: 5.3 },
}

describe('eight-template production workspace', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.stubGlobal('fetch', vi.fn(fetchResponse))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    window.localStorage.clear()
  })

  it('loads the native wizard, preview, model tree and four-column controls', async () => {
    render(createElement(App))

    expect(screen.getByRole('heading', { name: 'PackStudio' })).toBeInTheDocument()
    expect(await screen.findByText('1 个块')).toBeInTheDocument()
    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Die' })).toBeInTheDocument()
    expect(screen.getByLabelText('Die Length Ld')).toHaveValue(1.8)
    expect(screen.getByRole('separator', { name: '调整属性栏宽度' })).toHaveAttribute(
      'aria-valuenow',
      '390',
    )
    expect(screen.getByRole('tab', { name: '材料配置' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: '模型树' }))
    expect(screen.getByText('Package substrate')).toBeInTheDocument()
  })

  it('combines BGA removal and center solder without exposing staggered patterns', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: 'BGA 焊球配置' }))
    fireEvent.click(screen.getByRole('switch', { name: '焊球去除' }))
    fireEvent.click(screen.getByRole('switch', { name: '中央焊球' }))
    expect(screen.queryByText(/交错阵列/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    const body = requestBody(generateCalls().at(-1))
    expect(body.bga).toMatchObject({
      representation: 'equivalent',
      solder_removal_enabled: true,
      center_solder_enabled: true,
    })
  })

  it('sends native numeric overrides inside the implemented range and persists them', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.change(screen.getByLabelText('Die Length Ld'), { target: { value: '1.9' } })
    fireEvent.click(screen.getByRole('button', { name: '保存参数' }))
    expect(localStorage.getItem('packstudio.library.v2.flip_chip_cbga')).toContain('1.9')
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    expect(requestBody(generateCalls().at(-1)).overrides).toEqual({
      'flip_chip_cbga.die.length': 1.9,
    })
  })

  it('links fields through the native production condition key', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    expect(screen.queryByLabelText('顶盖厚度')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('顶部结构'), {
      target: { value: 'lid' },
    })
    expect(screen.getByLabelText('顶盖厚度')).toBeInTheDocument()
  })
})

function template(id: string, display_name: string, has_bga: boolean): TemplateCatalogItem {
  return {
    id,
    display_name,
    category: has_bga ? 'Ball Grid Arrays' : 'Other Parts',
    has_bga,
    bga_representations: has_bga ? ['equivalent', 'discrete'] : [],
    implementation_status: 'packstudio_native',
    runtime_reference_data_required: false,
  }
}

function fetchResponse(input: RequestInfo | URL) {
  const url = String(input)
  if (url === '/api/templates') return jsonResponse(catalog)
  if (url.endsWith('/schema')) return jsonResponse(schema)
  if (url.endsWith('/defaults')) return jsonResponse(defaults)
  if (url.endsWith('/materials')) return jsonResponse(generatedModel.materials)
  if (url.endsWith('/generate')) return jsonResponse(generatedModel)
  return Promise.resolve(new Response('', { status: 404 }))
}

const jsonResponse = (value: unknown) =>
  Promise.resolve({ ok: true, status: 200, json: async () => value } as Response)

const generateCalls = () =>
  vi.mocked(fetch).mock.calls.filter(([url]) => String(url).endsWith('/generate'))

function requestBody(call: [RequestInfo | URL, RequestInit?] | undefined) {
  return JSON.parse(String(call?.[1]?.body)) as TemplateRequest
}
