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

vi.mock('../../src/frontend/features/model-editor/ModelPreview', () => ({
  default: () => createElement('div', { 'aria-label': '测试三维模型' }),
}))

const catalog: TemplateCatalogItem[] = [
  template('cbga_fc', 'Flip Chip CBGA', true),
  template('bare_die', 'Bare Die', false),
]

const schema: TemplateSchema = {
  schema_version: 'packstudio.wizard/v2',
  template_id: 'cbga_fc',
  has_bga: true,
  special_rules: {
    outline_type: 'standard_outline',
    die_type: 'actual_type',
    bga_pattern: 'implicit_full_with_center_and_removal',
    flip_chip_bumps: 'thick_orthotropic_equivalent',
  },
  steps: [
    {
      id: 'package_setup',
      label: '封装规格',
      fields: [
        {
          target_id: 'cbga_fc.footprint.size',
          ui_location: 'package_setup',
          component: 'package_setup',
          label: 'Footprint 尺寸（JEDEC）',
          control: 'footprint',
          default: 'CBGAFC_49_6X6mm',
          options: ['CBGAFC_49_6X6mm', 'CBGAFC_81_8X8mm'],
          option_labels: {
            CBGAFC_49_6X6mm: 'CBGAFC · 49 球 · 6 × 6 mm',
            CBGAFC_81_8X8mm: 'CBGAFC · 81 球 · 8 × 8 mm',
          },
          preset_values: {
            CBGAFC_49_6X6mm: { 'cbga_fc.die.length': 1.8 },
            CBGAFC_81_8X8mm: { 'cbga_fc.die.length': 2.4 },
          },
          classification: 'jedec_preset',
          property_name: 'footprint.size',
          supported_values: ['CBGAFC_49_6X6mm', 'CBGAFC_81_8X8mm'],
          evidence_status: 'implemented',
          editable: true,
        },
      ],
    },
    {
      id: 'die',
      label: '芯片',
      fields: [
        {
          target_id: 'cbga_fc.cover.type',
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
          target_id: 'cbga_fc.lid.thickness',
          ui_location: 'die',
          component: 'package',
          label: '顶盖厚度',
          control: 'number',
          default: 0.3,
          minimum: 0.05,
          maximum: 3,
          options: [],
          classification: 'numeric_parameter',
          property_name: 'lid.thickness',
          supported_values: [0.05, 3],
          evidence_status: 'implemented',
          editable: true,
          visible_when: { 'cover.type': 'lid' },
        },
        {
          target_id: 'cbga_fc.die.length',
          ui_location: 'die',
          component: 'die',
          label: '芯片长度 Ld',
          control: 'number',
          default: 1.8,
          minimum: 1.62,
          maximum: 1.98,
          options: [],
          classification: 'numeric_parameter',
          property_name: 'dieLengthLd',
          supported_values: [1.62, 1.8, 1.98],
          evidence_status: 'implemented',
          editable: true,
        },
        {
          target_id: 'cbga_fc.material.die',
          ui_location: 'die',
          component: 'group-die',
          label: '芯片材料',
          control: 'material',
          default: 'silicon',
          options: ['silicon'],
          classification: 'material_option',
          property_name: 'material.group-die',
          supported_values: ['silicon'],
          evidence_status: 'implemented',
          editable: true,
          material_group_id: 'group-die',
        },
      ],
    },
    {
      id: 'solder_balls',
      label: 'BGA 焊球',
      fields: [],
    },
  ],
}

const defaults: TemplateRequest = {
  template_id: 'cbga_fc',
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
}

const generatedModel: PackageModel = {
  schema_version: 'packstudio.model/v1',
  template_id: 'cbga_fc',
  name: 'Flip Chip CBGA',
  length_unit: 'mm',
  coordinate_system: {
    origin: 'package bottom-plane center (FloTHERM PACK)',
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
    vi.stubGlobal('fetch', vi.fn(fetchResponse))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the native wizard, preview, model tree and four-column controls', async () => {
    render(createElement(App))

    expect(screen.getByRole('heading', { name: 'PackStudio' })).toBeInTheDocument()
    expect(await screen.findByText('1 个块')).toBeInTheDocument()
    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '概要' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    expect(screen.getByRole('heading', { name: '芯片' })).toBeInTheDocument()
    expect(screen.getByLabelText('芯片长度 Ld')).toHaveValue(1.8)
    expect(screen.getByRole('separator', { name: '调整属性栏宽度' })).toHaveAttribute(
      'aria-valuenow',
      '390',
    )
    expect(screen.getByRole('combobox', { name: '芯片材料' })).toHaveTextContent('silicon')
    expect(screen.getByText(/允许范围.*1.62.*1.98/)).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '材料库' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: '模型树' }))
    expect(screen.getByText('Package substrate')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '组件层级' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Layer 层级' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '建模选项' }))
    expect(screen.getByRole('combobox', { name: 'BGA 焊球阵列建模' })).toBeInTheDocument()
    expect(screen.queryByLabelText('最大网格尺寸预设')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '折叠 Flip Chip CBGA' }))
    expect(screen.queryByText('Package substrate')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '展开 Flip Chip CBGA' }))
    fireEvent.click(screen.getByRole('button', { name: '隐藏 Substrate' }))
    expect(screen.getByText('已隐藏')).toBeInTheDocument()
  })

  it('combines BGA removal and center solder without exposing staggered patterns', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '焊球去除' }))
    fireEvent.click(screen.getByRole('switch', { name: '中央去球' }))
    fireEvent.click(screen.getByRole('button', { name: '中央焊球' }))
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

  it('starts from template defaults each time the workspace is opened', async () => {
    const workspace = render(createElement(App))
    await screen.findByText('1 个块')
    expect(screen.queryByRole('button', { name: '保存参数' })).not.toBeInTheDocument()
    expect(screen.queryByText('参数已保存')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '边界条件' })).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('设计名称'), { target: { value: '当前修改' } })
    expect(screen.getByLabelText('设计名称')).toHaveValue('当前修改')
    workspace.unmount()
    render(createElement(App))
    await screen.findByText('1 个块')
    expect(screen.getByLabelText('设计名称')).toHaveValue(defaults.design_name)
    expect(requestBody(generateCalls().at(-1))).toEqual(defaults)
  })

  it('sends native numeric overrides inside the implemented range', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    fireEvent.change(screen.getByLabelText('芯片长度 Ld'), { target: { value: '1.9' } })
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    expect(requestBody(generateCalls().at(-1)).overrides).toEqual({
      'cbga_fc.die.length': 1.9,
    })
  })

  it('applies a footprint preset immediately and sends only the preset choice', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '封装规格' }))
    fireEvent.change(screen.getByLabelText('Footprint 尺寸（JEDEC）'), {
      target: { value: 'CBGAFC_81_8X8mm' },
    })
    expect(screen.getByText(/自动填充关联参数/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    expect(screen.getByLabelText('芯片长度 Ld')).toHaveValue(2.4)
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    expect(requestBody(generateCalls().at(-1)).overrides).toEqual({
      'cbga_fc.footprint.size': 'CBGAFC_81_8X8mm',
    })
  })

  it('keeps a manual dimension when it differs from the active footprint preset', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '封装规格' }))
    fireEvent.change(screen.getByLabelText('Footprint 尺寸（JEDEC）'), {
      target: { value: 'CBGAFC_81_8X8mm' },
    })
    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    fireEvent.change(screen.getByLabelText('芯片长度 Ld'), { target: { value: '1.8' } })
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))

    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    expect(requestBody(generateCalls().at(-1)).overrides).toEqual({
      'cbga_fc.footprint.size': 'CBGAFC_81_8X8mm',
      'cbga_fc.die.length': 1.8,
    })
  })

  it('links fields through the native production condition key', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')

    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    expect(screen.queryByLabelText('顶盖厚度')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('顶部结构'), {
      target: { value: 'lid' },
    })
    expect(screen.getByLabelText('顶盖厚度')).toBeInTheDocument()
  })

  it('edits material properties as design overrides without changing component binding', async () => {
    render(createElement(App))
    await screen.findByText('1 个块')
    fireEvent.click(screen.getByRole('button', { name: '芯片' }))
    fireEvent.change(screen.getByLabelText('kx'), { target: { value: '18' } })
    fireEvent.click(screen.getByRole('button', { name: '生成模型' }))
    await waitFor(() => expect(generateCalls()).toHaveLength(2))
    const body = requestBody(generateCalls().at(-1))
    expect(body.custom_materials[0]).toMatchObject({
      id: 'alumina',
      conductivity: { x: 18, y: 16, z: 16 },
    })
    expect(body.material_assignments).toEqual({})
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
const jsonResponse = (value: unknown) => Promise.resolve(
  { ok: true, status: 200, json: async () => value } as Response,
)
const generateCalls = () =>
  vi.mocked(fetch).mock.calls.filter(([url]) => String(url).endsWith('/generate'))
function requestBody(call: [RequestInfo | URL, RequestInit?] | undefined) {
  return JSON.parse(String(call?.[1]?.body)) as TemplateRequest
}
