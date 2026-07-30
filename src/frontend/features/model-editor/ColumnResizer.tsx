import { useRef, type PointerEvent } from 'react'

interface ColumnResizerProps {
  value: number
  onChange: (value: number) => void
  ariaLabel: string
  placement: 'property' | 'inspector'
  deltaDirection?: 1 | -1
  minimum?: number
  maximum?: number
}

export default function ColumnResizer({
  value,
  onChange,
  ariaLabel,
  placement,
  deltaDirection = 1,
  minimum = 300,
  maximum = 600,
}: ColumnResizerProps) {
  const dragStart = useRef<{ pointerX: number; width: number } | null>(null)
  const clamp = (next: number) => Math.min(maximum, Math.max(minimum, next))

  const startDrag = (event: PointerEvent<HTMLDivElement>) => {
    dragStart.current = { pointerX: event.clientX, width: value }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  const moveDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (dragStart.current === null) return
    const pointerDelta = event.clientX - dragStart.current.pointerX
    onChange(clamp(dragStart.current.width + pointerDelta * deltaDirection))
  }
  const stopDrag = (event: PointerEvent<HTMLDivElement>) => {
    dragStart.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  return (
    <div
      className={`column-resizer column-resizer-${placement}`}
      role="separator"
      aria-label={ariaLabel}
      aria-orientation="vertical"
      aria-valuemin={minimum}
      aria-valuemax={maximum}
      aria-valuenow={value}
      tabIndex={0}
      onPointerDown={startDrag}
      onPointerMove={moveDrag}
      onPointerUp={stopDrag}
      onPointerCancel={stopDrag}
      onKeyDown={(event) => {
        if (event.key === 'ArrowLeft') onChange(clamp(value - 20 * deltaDirection))
        if (event.key === 'ArrowRight') onChange(clamp(value + 20 * deltaDirection))
      }}
    />
  )
}
