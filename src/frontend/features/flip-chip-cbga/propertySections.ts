export type PropertySectionId =
  | 'summary'
  | 'substrate'
  | 'die'
  | 'encapsulant'
  | 'flip_chip_bumps'
  | 'solder_balls'
  | 'solder_pattern'
  | 'lid'
  | 'heat_slug'
  | 'mesh'
  | 'boundaries'
  | 'modeling_options'

export const propertySections: Array<{
  id: PropertySectionId
  label: string
}> = [
  { id: 'summary', label: '汇总' },
  { id: 'substrate', label: '封装基底' },
  { id: 'die', label: '芯片' },
  { id: 'encapsulant', label: '塑封' },
  { id: 'flip_chip_bumps', label: '倒装芯片凸块' },
  { id: 'solder_balls', label: '焊球' },
  { id: 'solder_pattern', label: '焊球样式' },
  { id: 'lid', label: '顶盖' },
  { id: 'heat_slug', label: '插入式散热块' },
  { id: 'mesh', label: '网格尺寸' },
  { id: 'boundaries', label: '边界条件' },
  { id: 'modeling_options', label: '建模选项' },
]

export const propertySection = (id: PropertySectionId) =>
  propertySections.find((section) => section.id === id) ?? propertySections[0]
