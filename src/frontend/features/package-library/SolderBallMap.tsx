import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import type { BgaConfiguration } from './types'

export default function SolderBallMap({ value, onChange }: {
  value: BgaConfiguration; onChange: (value: BgaConfiguration) => void
}) {
  const [error, setError] = useState('')
  const [text, setText] = useState<string | null>(null)
  const importText = (source: string) => {
    setText(source)
    try {
      const lines = source.trim() ? source.trim().split(/\r?\n/) : []
      const data = lines.filter((line, i) => i !== 0 || !/^\s*(id|name)\s*[,;\t]/i.test(line))
      const ball_map = data.map((line) => {
        const cells = line.split(/[,;\t]/).map((v) => v.trim())
        if (cells.length !== 3 || !cells[0] || !cells[1] || !cells[2]
          || !Number.isFinite(Number(cells[1])) || !Number.isFinite(Number(cells[2]))) {
          throw new Error('每行需要 ID、X、Y 三列；坐标单位 mm。')
        }
        return { id: cells[0], x: Number(cells[1]), y: Number(cells[2]) }
      })
      if (new Set(ball_map.map((p) => p.id)).size !== ball_map.length) throw new Error('ID 必须唯一。')
      onChange({ ...value, ball_map, representation: 'discrete' })
      setError('')
    } catch (reason) { setError(String(reason)) }
  }
  return <Stack spacing={1}>
    <FormControlLabel label="主阵列 Staggered" control={<Switch checked={value.staggered ?? false}
      onChange={(e) => onChange({ ...value, staggered: e.target.checked })} />} />
    <FormControlLabel label="Solder Ball Map" control={<Switch checked={value.ball_map_enabled ?? false}
      onChange={(e) => onChange({ ...value, ball_map_enabled: e.target.checked,
        representation: e.target.checked ? 'discrete' : value.representation })} />} />
    {value.ball_map_enabled && <>
      <Alert severity="info">球位图覆盖主阵列、去球和中央加球。空表输出零个焊球。</Alert>
      <TextField multiline minRows={3} label="ID, X (mm), Y (mm)"
        value={text ?? (value.ball_map ?? []).map((p) => `${p.id},${p.x},${p.y}`).join('\n')}
        onChange={(e) => importText(e.target.value)} />
      <Button component="label">导入 CSV<input hidden type="file" accept=".csv,.txt"
        onChange={async (e) => { const f = e.target.files?.[0]; if (f) importText(await f.text()) }} /></Button>
      {error && <Alert severity="error">{error}</Alert>}
    </>}
  </Stack>
}
