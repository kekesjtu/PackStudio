import { Fragment, useMemo, type CSSProperties } from 'react'

import FieldShell from '../../ui/FieldShell'
import type { CellIndex } from './types'

interface SolderRemovalMatrixProps {
  rows: number
  columns: number
  omittedCells: CellIndex[]
  removalRows: number
  removalColumns: number
  onChange: (cells: CellIndex[]) => void
}

interface CellBounds {
  rowStart: number
  rowEnd: number
  columnStart: number
  columnEnd: number
}

export default function SolderRemovalMatrix({
  rows,
  columns,
  omittedCells,
  removalRows,
  removalColumns,
  onChange,
}: SolderRemovalMatrixProps) {
  const matrixRows = clampDimension(rows)
  const matrixColumns = clampDimension(columns)
  const cellSize = Math.max(14, Math.min(34, Math.floor(280 / Math.max(matrixRows, matrixColumns))))
  const matrixStyle = {
    '--matrix-columns': matrixColumns,
    '--matrix-cell': `${cellSize}px`,
  } as CSSProperties
  const selected = useMemo(() => {
    const keys = new Set<string>()
    return omittedCells.filter((cell) => {
      const key = cellKey(cell)
      if (!isInsideArray(cell, matrixRows, matrixColumns) || keys.has(key)) return false
      keys.add(key)
      return true
    })
  }, [omittedCells, matrixRows, matrixColumns])
  const selectedKeys = useMemo(() => new Set(selected.map(cellKey)), [selected])
  const removalBounds = useMemo(
    () => centeredBounds(matrixRows, matrixColumns, removalRows, removalColumns),
    [matrixRows, matrixColumns, removalRows, removalColumns],
  )

  const toggle = (row: number, column: number) => {
    const key = cellKey({ row, column })
    const next = selectedKeys.has(key)
      ? selected.filter((cell) => cellKey(cell) !== key)
      : [...selected, { row, column }]
    onChange(
      next
        .filter((cell) => isInsideArray(cell, matrixRows, matrixColumns))
        .sort((left, right) => left.row - right.row || left.column - right.column),
    )
  }

  return (
    <FieldShell
      label="显式去球单元"
      unit={`已选 ${selected.length} 个`}
      hint="点击矩阵单元添加或取消显式去球；斜纹单元已被去球区覆盖。行列编号从 0 开始。"
    >
      <div
        className="solder-matrix"
        role="group"
        aria-label={`显式去球矩阵，${matrixRows} 行 ${matrixColumns} 列`}
      >
        <div className="solder-matrix-grid" style={matrixStyle}>
          <span className="solder-matrix-corner" aria-hidden="true">Y/X</span>
          {range(matrixColumns).map((column) => (
            <span key={`column-${column}`} className="solder-matrix-column-index" aria-hidden="true">
              {column}
            </span>
          ))}
          {range(matrixRows).map((row) => (
            <Fragment key={`row-${row}`}>
              <span className="solder-matrix-row-index" aria-hidden="true">{row}</span>
              {range(matrixColumns).map((column) => {
                const explicit = selectedKeys.has(cellKey({ row, column }))
                const covered = !explicit && isCovered(row, column, removalBounds)
                const state = explicit ? 'omitted' : covered ? 'region' : 'present'
                const action = explicit
                  ? '取消显式去球'
                  : covered
                    ? '已被去球区覆盖'
                    : '添加显式去球'
                return (
                  <button
                    key={`cell-${row}-${column}`}
                    type="button"
                    className="solder-matrix-cell"
                    data-state={state}
                    aria-pressed={explicit}
                    aria-label={`行 ${row}，列 ${column}，${action}`}
                    title={`行 ${row}，列 ${column}：${action}`}
                    disabled={covered}
                    onClick={() => toggle(row, column)}
                  >
                    <span className="solder-matrix-ball" aria-hidden="true" />
                  </button>
                )
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <div className="solder-matrix-legend" aria-hidden="true">
        <span><i data-kind="present" />可点击</span>
        <span><i data-kind="omitted" />显式去球</span>
        <span><i data-kind="region" />去球区覆盖</span>
      </div>
    </FieldShell>
  )
}

function clampDimension(value: number) {
  if (!Number.isFinite(value)) return 1
  return Math.max(1, Math.min(50, Math.trunc(value)))
}

function isInsideArray(cell: CellIndex, rows: number, columns: number) {
  return cell.row >= 0 && cell.row < rows && cell.column >= 0 && cell.column < columns
}

function centeredBounds(
  rows: number,
  columns: number,
  regionRows: number,
  regionColumns: number,
): CellBounds | null {
  if (regionRows <= 0 || regionColumns <= 0) return null
  const rowStart = Math.floor((rows - regionRows) / 2)
  const columnStart = Math.floor((columns - regionColumns) / 2)
  return {
    rowStart,
    rowEnd: rowStart + regionRows,
    columnStart,
    columnEnd: columnStart + regionColumns,
  }
}

function isCovered(row: number, column: number, bounds: CellBounds | null) {
  return bounds !== null &&
    row >= bounds.rowStart && row < bounds.rowEnd &&
    column >= bounds.columnStart && column < bounds.columnEnd
}

function cellKey(cell: CellIndex) {
  return `${cell.row}:${cell.column}`
}

function range(length: number) {
  return Array.from({ length }, (_, index) => index)
}
