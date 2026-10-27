import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import MaterialLibraryBrowser from '../../src/frontend/features/package-library/MaterialLibraryBrowser'
import { safe } from './materialQualityFixtures'

const copper = { ...safe, id: 'copper', name: 'Copper', category: 'Metals' }
const gold = { ...safe, id: 'gold', name: 'Gold', category: 'Metals' }
const ceramic = { ...safe, id: 'ceramic', name: 'Ceramic', category: 'Ceramics' }

describe('material library browsing', () => {
  it('lists all materials in native category order with a fallback group', () => {
    render(<MaterialLibraryBrowser materials={[copper, safe, gold, ceramic]} onChange={vi.fn()} />)
    expect(screen.getAllByRole('heading').map((heading) => heading.textContent)).toEqual([
      'Ceramics (1)', 'Metals (2)', 'Others (1)',
    ])
    const metals = within(screen.getByRole('list', { name: 'Metals' }))
    expect(metals.getByRole('button', { name: 'Copper copper' })).toBeInTheDocument()
    expect(metals.getByRole('button', { name: 'Gold gold' })).toBeInTheDocument()
    expect(screen.getAllByRole('button')).toHaveLength(4)
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('kx')).not.toBeInTheDocument()
  })

  it('opens properties only after selection and edits the selected material', () => {
    const onChange = vi.fn()
    const { rerender } = render(<MaterialLibraryBrowser materials={[copper, gold]} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: 'Gold gold' }))
    expect(screen.getByRole('region', { name: '材料属性' })).toBeInTheDocument()
    expect(screen.getByLabelText('名称')).toHaveValue('Gold')
    fireEvent.change(screen.getByLabelText('kx'), { target: { value: '123.5' } })
    expect(onChange).toHaveBeenCalledWith({ ...gold, conductivity: { ...gold.conductivity, x: 123.5 } })
    fireEvent.click(screen.getByRole('button', { name: 'Copper copper' }))
    expect(screen.getByLabelText('名称')).toHaveValue('Copper')
    rerender(<MaterialLibraryBrowser materials={[gold]} onChange={onChange} />)
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
  })
})
