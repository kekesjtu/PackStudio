import Alert from '@mui/material/Alert'
import AlertTitle from '@mui/material/AlertTitle'

import type { MaterialQualityIssue } from './materialQuality'

export default function MaterialQualityWarning({ issues }: { issues: MaterialQualityIssue[] }) {
  if (!issues.length) return null
  return (
    <Alert severity="warning" sx={{ maxHeight: 220, overflowY: 'auto', flexShrink: 0 }}>
      <AlertTitle>材料热容数据警告</AlertTitle>
      密度、比热存在非真实值风险：以下属性为 1，按疑似占位值提示。
      <ul>
        {issues.map(({ material, properties }) => (
          <li key={material.id}>{material.name}（{material.id}）：{properties.join('；')}</li>
        ))}
      </ul>
      这些值仍会参与等效热容计算，等效结果不为 1 也不代表热容可信。
      用于瞬态分析前，请在当前方案中补齐真实物性后重新生成、导出。导出仍保留当前数值。
    </Alert>
  )
}
