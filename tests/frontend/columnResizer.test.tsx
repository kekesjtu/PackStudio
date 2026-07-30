import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import ColumnResizer from '../../src/frontend/features/model-editor/ColumnResizer'

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

function ResizerHarness({ deltaDirection = 1 }: { deltaDirection?: 1 | -1 }) {
  const [value, setValue] = useState(380)
  return (
    <ColumnResizer
      value={value}
      onChange={setValue}
      ariaLabel="测试栏宽"
      placement="property"
      deltaDirection={deltaDirection}
    />
  )
}

describe('ColumnResizer', () => {
  it('resizes a column through pointer dragging', () => {
    render(<ResizerHarness />)
    const separator = screen.getByRole('separator', { name: '测试栏宽' })

    fireEvent.pointerDown(separator, { pointerId: 1, clientX: 100 })
    fireEvent.pointerMove(separator, { pointerId: 1, clientX: 135 })
    fireEvent.pointerUp(separator, { pointerId: 1, clientX: 135 })

    expect(separator).toHaveAttribute('aria-valuenow', '415')
  })

  it('reverses physical movement for a right-side inspector', () => {
    render(<ResizerHarness deltaDirection={-1} />)
    const separator = screen.getByRole('separator', { name: '测试栏宽' })

    fireEvent.keyDown(separator, { key: 'ArrowLeft' })

    expect(separator).toHaveAttribute('aria-valuenow', '400')
  })
})
