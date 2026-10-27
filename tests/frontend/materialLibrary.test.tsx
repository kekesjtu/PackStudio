import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import MaterialLibraryBrowser from '../../src/frontend/features/package-library/MaterialLibraryBrowser'
import { safe } from './materialQualityFixtures'

const copper = { ...safe, id: 'copper', name: 'Copper', category: 'Metals' }
const gold = { ...safe, id: 'gold', name: 'Gold', category: 'Metals' }
const ceramic = { ...safe, id: 'ceramic', name: 'Ceramic', category: 'Ceramics' }

describe('material library browsing', () => {
  it('starts with every category collapsed in native order, including the fallback group', () => {
    render(<MaterialLibraryBrowser materials={[copper, safe, gold, ceramic]} onChange={vi.fn()} />)
    expect(screen.getAllByRole('button').map((button) => button.getAttribute('aria-label'))).toEqual([
      '展开 Ceramics', '展开 Metals', '展开 Others',
    ])
    for (const button of screen.getAllByRole('button')) expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('list', { name: 'Metals' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Copper copper' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '展开 Metals' })).toHaveTextContent('(2)')
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('kx')).not.toBeInTheDocument()
  })

  it('expands and collapses each category independently without opening material properties', () => {
    render(<MaterialLibraryBrowser materials={[copper, safe, gold, ceramic]} onChange={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: '展开 Metals' }))
    const metals = within(screen.getByRole('list', { name: 'Metals' }))
    expect(metals.getByRole('button', { name: 'Copper copper' })).toBeInTheDocument()
    expect(metals.getByRole('button', { name: 'Gold gold' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '展开 Ceramics' }))
    expect(screen.getByRole('button', { name: 'Ceramic ceramic' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '折叠 Metals' }))
    expect(screen.queryByRole('button', { name: 'Gold gold' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ceramic ceramic' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('kx')).not.toBeInTheDocument()
  })

  it('opens properties only after selection and edits the selected material', () => {
    const onChange = vi.fn()
    const { rerender } = render(<MaterialLibraryBrowser materials={[copper, gold]} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: '展开 Metals' }))
    fireEvent.click(screen.getByRole('button', { name: 'Gold gold' }))
    expect(screen.getByRole('region', { name: '材料属性' })).toBeInTheDocument()
    expect(screen.getByLabelText('名称')).toHaveValue('Gold')
    fireEvent.change(screen.getByLabelText('kx'), { target: { value: '123.5' } })
    expect(onChange).toHaveBeenCalledWith({ ...gold, conductivity: { ...gold.conductivity, x: 123.5 } })
    fireEvent.click(screen.getByRole('button', { name: '折叠 Metals' }))
    expect(screen.getByLabelText('名称')).toHaveValue('Gold')
    fireEvent.click(screen.getByRole('button', { name: '展开 Metals' }))
    fireEvent.click(screen.getByRole('button', { name: 'Copper copper' }))
    expect(screen.getByLabelText('名称')).toHaveValue('Copper')
    rerender(<MaterialLibraryBrowser materials={[gold]} onChange={onChange} />)
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
  })

  it('deselects a material on a second left click and keeps the category expanded', () => {
    const onChange = vi.fn()
    render(<MaterialLibraryBrowser materials={[copper, gold]} onChange={onChange} />)
    fireEvent.click(screen.getByRole('button', { name: '展开 Metals' }))
    const copperRow = screen.getByRole('button', { name: 'Copper copper' })
    fireEvent.click(copperRow)
    expect(screen.getByLabelText('名称')).toHaveValue('Copper')
    fireEvent.click(copperRow)
    expect(screen.queryByRole('region', { name: '材料属性' })).not.toBeInTheDocument()
    expect(copperRow).not.toHaveClass('Mui-selected')
    expect(screen.getByRole('button', { name: '折叠 Metals' })).toBeInTheDocument()
    expect(onChange).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Gold gold' }))
    expect(screen.getByLabelText('名称')).toHaveValue('Gold')
  })
})
