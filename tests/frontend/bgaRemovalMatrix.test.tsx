import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import BgaConfigurationPanel from '../../src/frontend/features/package-library/BgaConfigurationPanel'
import type { BgaConfiguration } from '../../src/frontend/features/package-library/types'

const pattern: BgaConfiguration = {
  representation: 'equivalent',
  center_solder_enabled: false,
  center_solder_rows: 1,
  center_solder_columns: 1,
  solder_removal_enabled: true,
  removal_rows: 0,
  removal_columns: 0,
  omitted_cells: [],
  allow_asymmetric_regions: false,
}

describe('BGA solder removal matrix', () => {
  it('hides explicit removal controls while solder removal is disabled', () => {
    render(
      <BgaConfigurationPanel
        value={{ ...pattern, solder_removal_enabled: false }}
        section="removal"
        rows={3}
        columns={4}
        onChange={vi.fn()}
      />,
    )
    expect(screen.queryByText('显式去球单元')).not.toBeInTheDocument()
    expect(screen.queryByRole('group', { name: /显式去球矩阵/ })).not.toBeInTheDocument()
  })

  it('adds and clears explicit removal cells by clicking matrix units', () => {
    const onChange = vi.fn()
    const props = { section: 'removal' as const, rows: 3, columns: 4, onChange }
    const { rerender } = render(<BgaConfigurationPanel value={pattern} {...props} />)

    fireEvent.click(screen.getByRole('button', { name: '行 1，列 2，添加显式去球' }))
    const next = onChange.mock.calls[0][0] as BgaConfiguration
    expect(next.omitted_cells).toEqual([{ row: 1, column: 2 }])

    rerender(<BgaConfigurationPanel value={next} {...props} />)
    const selected = screen.getByRole('button', { name: '行 1，列 2，取消显式去球' })
    expect(selected).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(selected)
    expect(onChange.mock.calls[1][0].omitted_cells).toEqual([])
  })

  it('marks cells covered by the centered removal region as unavailable', () => {
    render(
      <BgaConfigurationPanel
        value={{ ...pattern, removal_rows: 1, removal_columns: 1 }}
        section="removal"
        rows={3}
        columns={3}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: '行 1，列 1，已被去球区覆盖' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '行 0，列 0，添加显式去球' })).toBeEnabled()
  })
})
