import { createElement } from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from '../../src/frontend/App'

describe('PackStudio scaffold', () => {
  it('shows the guided modeling workspace', () => {
    render(createElement(App))

    expect(screen.getByRole('heading', { name: 'PackStudio' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '封装参数' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '三维预览' })).toBeInTheDocument()
  })
})
