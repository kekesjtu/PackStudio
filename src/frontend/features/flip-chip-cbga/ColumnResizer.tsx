import { useRef, type PointerEvent } from 'react'

interface ColumnResizerProps {
  value: number
  onChange: (value: number) => void
  minimum?: number
  maximum?: number
}

export default function ColumnResizer({
  value,
  onChange,
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
    onChange(clamp(dragStart.current.width + event.clientX - dragStart.current.pointerX))
  }
  const stopDrag = (event: PointerEvent<HTMLDivElement>) => {
    dragStart.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  return (
    <div
      className="column-resizer"
      role="separator"
      aria-label="调整属性与三维视图宽度"
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
        if (event.key === 'ArrowLeft') onChange(clamp(value - 20))
        if (event.key === 'ArrowRight') onChange(clamp(value + 20))
      }}
    />
  )
}
