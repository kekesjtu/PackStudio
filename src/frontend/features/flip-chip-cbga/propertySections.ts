export type PropertySectionId =
  | 'summary'
  | 'substrate'
  | 'die'
  | 'encapsulant'
  | 'flip_chip_bumps'
  | 'solder_balls'
  | 'solder_removal'
  | 'center_solder'
  | 'lid'
  | 'heat_slug'
  | 'modeling_options'

export const propertySections: Array<{
  id: PropertySectionId
  label: string
  description: string
}> = [
  { id: 'summary', label: '汇总', description: '设计名称、模型状态与输出摘要' },
  { id: 'substrate', label: '封装基底', description: '基板尺寸和材料绑定' },
  { id: 'die', label: '芯片', description: '芯片尺寸、功率和材料' },
  { id: 'encapsulant', label: '塑封', description: '可选的 Die 外围塑封环' },
  { id: 'flip_chip_bumps', label: '倒装芯片凸块', description: '凸块阵列、Underfill 和材料' },
  { id: 'solder_balls', label: '焊球', description: 'BGA 焊球阵列尺寸和材料' },
  { id: 'solder_removal', label: '焊球去除', description: '去球模式、空缺区域和自定义单元' },
  { id: 'center_solder', label: '中央焊球', description: '中央焊球分区及行列数' },
  { id: 'lid', label: '顶盖', description: '可选顶盖和热界面材料' },
  { id: 'heat_slug', label: '插入式散热块', description: '可选散热块和热界面材料' },
  { id: 'modeling_options', label: '建模选项', description: '离散/等效表达和边界条件' },
]

export const propertySection = (id: PropertySectionId) =>
  propertySections.find((section) => section.id === id) ?? propertySections[0]
