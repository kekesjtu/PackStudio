import { GizmoHelper, useGizmoContext } from '@react-three/drei/core/GizmoHelper'
import { useMemo, useState } from 'react'
import { CanvasTexture, SRGBColorSpace, Vector3 } from 'three'

type AxisTuple = [number, number, number]

interface AxisDefinition {
  label: string
  color: string
  direction: AxisTuple
  shaftPosition: AxisTuple
  shaftRotation: AxisTuple
  conePosition: AxisTuple
  coneRotation: AxisTuple
  tagPosition: AxisTuple
}

const AXES: AxisDefinition[] = [
  {
    label: 'X',
    color: '#a84a3c',
    direction: [1, 0, 0],
    shaftPosition: [0.42, 0, 0],
    shaftRotation: [0, 0, -Math.PI / 2],
    conePosition: [0.9, 0, 0],
    coneRotation: [0, 0, -Math.PI / 2],
    tagPosition: [1.22, 0, 0],
  },
  {
    label: 'Y',
    color: '#5d7d4c',
    direction: [0, 1, 0],
    shaftPosition: [0, 0.42, 0],
    shaftRotation: [0, 0, 0],
    conePosition: [0, 0.9, 0],
    coneRotation: [0, 0, 0],
    tagPosition: [0, 1.22, 0],
  },
  {
    label: 'Z',
    color: '#466f8e',
    direction: [0, 0, 1],
    shaftPosition: [0, 0, 0.42],
    shaftRotation: [Math.PI / 2, 0, 0],
    conePosition: [0, 0, 0.9],
    coneRotation: [Math.PI / 2, 0, 0],
    tagPosition: [0, 0, 1.22],
  },
]

const TAG_SCALE = 0.5
const TAG_TEXTURE_SIZE = 96

export default function IndustrialGizmo() {
  return (
    <GizmoHelper alignment="bottom-right" margin={[66, 66]}>
      <group scale={38}>
        {AXES.map((axis) => (
          <group key={axis.label}>
            <mesh position={axis.shaftPosition} rotation={axis.shaftRotation}>
              <cylinderGeometry args={[0.018, 0.018, 0.84, 8]} />
              <meshBasicMaterial color={axis.color} toneMapped={false} />
            </mesh>
            <mesh position={axis.conePosition} rotation={axis.coneRotation}>
              <coneGeometry args={[0.07, 0.16, 14]} />
              <meshBasicMaterial color={axis.color} toneMapped={false} />
            </mesh>
            <AxisTag axis={axis} />
          </group>
        ))}
        <mesh>
          <boxGeometry args={[0.07, 0.07, 0.07]} />
          <meshBasicMaterial color="#354751" toneMapped={false} />
        </mesh>
      </group>
    </GizmoHelper>
  )
}

function AxisTag({ axis }: { axis: AxisDefinition }) {
  const { tweenCamera } = useGizmoContext()
  const [active, setActive] = useState(false)
  const texture = useMemo(
    () => createTagTexture(axis.label, axis.color),
    [axis.label, axis.color],
  )
  const direction = useMemo(() => new Vector3(...axis.direction), [axis.direction])
  const scale = TAG_SCALE * (active ? 1.12 : 1)

  return (
    <sprite
      position={axis.tagPosition}
      scale={scale}
      onPointerOver={(event) => {
        event.stopPropagation()
        setActive(true)
      }}
      onPointerOut={() => setActive(false)}
      onPointerDown={(event) => {
        event.stopPropagation()
        tweenCamera(direction)
      }}
    >
      <spriteMaterial
        map={texture}
        transparent
        depthWrite={false}
        toneMapped={false}
      />
    </sprite>
  )
}

function createTagTexture(label: string, color: string) {
  const canvas = document.createElement('canvas')
  canvas.width = TAG_TEXTURE_SIZE
  canvas.height = TAG_TEXTURE_SIZE
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Canvas 2D context is unavailable')

  const inset = 10
  const size = TAG_TEXTURE_SIZE - inset * 2
  context.fillStyle = '#273942'
  context.fillRect(inset, inset, size, size)
  context.strokeStyle = color
  context.lineWidth = 5
  context.strokeRect(inset, inset, size, size)
  context.fillStyle = '#f3f7f9'
  context.font = '700 48px Bahnschrift, "Segoe UI", sans-serif'
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.fillText(label, TAG_TEXTURE_SIZE / 2, TAG_TEXTURE_SIZE / 2 + 2)

  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  return texture
}

