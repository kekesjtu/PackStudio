import { useRef, type PointerEvent, type RefObject } from 'react'

interface RowResizerProps {
  value: number
  onChange: (value: number) => void
  containerRef: RefObject<HTMLElement | null>
  ariaLabel: string
  minimum?: number
  maximum?: number
  siblingMinimum?: number
}

export default function RowResizer({
  value,
  onChange,
  containerRef,
  ariaLabel,
  minimum = 120,
  maximum = 520,
  siblingMinimum = 180,
}: RowResizerProps) {
  const dragStart = useRef<{ pointerY: number; height: number } | null>(null)
  const availableMaximum = () => {
    const containerHeight = containerRef.current?.clientHeight ?? 0
    if (containerHeight <= 0) return maximum
    return Math.min(maximum, Math.max(minimum, containerHeight - siblingMinimum - 8))
  }
  const clamp = (next: number) => Math.min(availableMaximum(), Math.max(minimum, next))

  const startDrag = (event: PointerEvent<HTMLDivElement>) => {
    dragStart.current = { pointerY: event.clientY, height: value }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  const moveDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (dragStart.current === null) return
    onChange(clamp(dragStart.current.height + event.clientY - dragStart.current.pointerY))
  }
  const stopDrag = (event: PointerEvent<HTMLDivElement>) => {
    dragStart.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  return (
    <div
      className="row-resizer"
      role="separator"
      aria-label={ariaLabel}
      aria-orientation="horizontal"
      aria-valuemin={minimum}
      aria-valuemax={maximum}
      aria-valuenow={value}
      tabIndex={0}
      onPointerDown={startDrag}
      onPointerMove={moveDrag}
      onPointerUp={stopDrag}
      onPointerCancel={stopDrag}
      onKeyDown={(event) => {
        if (event.key === 'ArrowUp') onChange(clamp(value - 20))
        if (event.key === 'ArrowDown') onChange(clamp(value + 20))
      }}
    />
  )
}
