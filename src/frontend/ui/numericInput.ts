import type { FocusEvent } from 'react'

import './numeric-input.css'

export default function numericInput(integer = false) {
  return {
    'data-numeric-kind': integer ? 'integer' : 'decimal',
    inputMode: integer ? 'numeric' as const : 'decimal' as const,
    step: integer ? 1 : 'any',
    onFocus: (event: FocusEvent<HTMLInputElement>) => event.currentTarget.select(),
  }
}
