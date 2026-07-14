import { useRef, useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import RowResizer from '../../src/frontend/features/flip-chip-cbga/RowResizer'

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, 'setPointerCapture', {
    configurable: true,
    value: vi.fn(),
  })
  Object.defineProperty(HTMLElement.prototype, 'hasPointerCapture', {
    configurable: true,
    value: vi.fn(() => true),
  })
  Object.defineProperty(HTMLElement.prototype, 'releasePointerCapture', {
    configurable: true,
    value: vi.fn(),
  })
})

function ResizerHarness() {
  const [value, setValue] = useState(240)
  const containerRef = useRef<HTMLDivElement>(null)
  return (
    <div ref={containerRef}>
      <RowResizer
        value={value}
        onChange={setValue}
        containerRef={containerRef}
        ariaLabel="测试材料栏高"
      />
    </div>
  )
}

describe('RowResizer', () => {
  it('resizes material rows through pointer dragging', () => {
    render(<ResizerHarness />)
    const separator = screen.getByRole('separator', { name: '测试材料栏高' })

    fireEvent.pointerDown(separator, { pointerId: 1, clientY: 100 })
    fireEvent.pointerMove(separator, { pointerId: 1, clientY: 135 })
    fireEvent.pointerUp(separator, { pointerId: 1, clientY: 135 })

    expect(separator).toHaveAttribute('aria-valuenow', '275')
  })

  it('supports vertical keyboard resizing', () => {
    render(<ResizerHarness />)
    const separator = screen.getByRole('separator', { name: '测试材料栏高' })

    fireEvent.keyDown(separator, { key: 'ArrowUp' })

    expect(separator).toHaveAttribute('aria-valuenow', '220')
  })
})
