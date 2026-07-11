import { Bounds, Edges, OrbitControls } from '@react-three/drei'
import { Canvas, type ThreeEvent } from '@react-three/fiber'
import { Box, Typography } from '@mui/material'

import type { AxisAlignedBlock, Material, PackageModel } from './types'

interface ModelPreviewProps {
  model: PackageModel | null
  selectedBlockId: string | null
  onSelectBlock: (blockId: string | null) => void
}

interface PackageBlockProps {
  block: AxisAlignedBlock
  material: Material | undefined
  selected: boolean
  onSelect: (blockId: string) => void
}

const translucentStructures = new Set(['underfill', 'solder_ball_matrix'])

function PackageBlock({ block, material, selected, onSelect }: PackageBlockProps) {
  const position: [number, number, number] = [
    block.origin.x + block.size.x / 2,
    block.origin.z + block.size.z / 2,
    -(block.origin.y + block.size.y / 2),
  ]
  const size: [number, number, number] = [block.size.x, block.size.z, block.size.y]
  const translucent = translucentStructures.has(block.structure_type)

  const handlePointerDown = (event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation()
    onSelect(block.id)
  }

  return (
    <mesh position={position} onPointerDown={handlePointerDown}>
      <boxGeometry args={size} />
      <meshStandardMaterial
        color={selected ? '#ff9f1c' : (material?.color ?? '#78909c')}
        transparent={translucent}
        opacity={translucent ? 0.58 : 0.92}
        roughness={0.62}
        metalness={block.structure_type === 'heat_slug' ? 0.45 : 0.08}
      />
      <Edges color={selected ? '#8a4100' : '#20323d'} threshold={15} />
    </mesh>
  )
}

export default function ModelPreview({
  model,
  selectedBlockId,
  onSelectBlock,
}: ModelPreviewProps) {
  if (model === null) {
    return (
      <Box className="preview-empty" aria-label="模型预览等待区">
        <Typography color="text.secondary">生成模型后在此检查三维矩形块。</Typography>
      </Box>
    )
  }

  const materials = new Map(model.materials.map((material) => [material.id, material]))
  const minimumZ = Math.min(...model.blocks.map((block) => block.origin.z))
  const gridSize = Math.max(
    2,
    ...model.blocks.flatMap((block) => [block.size.x, block.size.y]),
  ) * 1.8

  return (
    <Box className="model-canvas" aria-label="Flip Chip CBGA 三维模型">
      <Canvas
        camera={{ position: [8, 6.5, 9], fov: 38, near: 0.01, far: 1000 }}
        onPointerMissed={() => onSelectBlock(null)}
      >
        <color attach="background" args={['#f7fafb']} />
        <ambientLight intensity={1.15} />
        <directionalLight position={[5, 10, 7]} intensity={1.8} />
        <directionalLight position={[-5, 2, -4]} intensity={0.6} />
        <Bounds fit clip observe margin={1.22}>
          {model.blocks.map((block) => (
            <PackageBlock
              key={block.id}
              block={block}
              material={materials.get(block.material_id)}
              selected={block.id === selectedBlockId}
              onSelect={onSelectBlock}
            />
          ))}
        </Bounds>
        <gridHelper
          args={[gridSize, 28, '#9fb2bc', '#d9e3e8']}
          position={[0, minimumZ - 0.02, 0]}
        />
        <OrbitControls makeDefault enableDamping />
      </Canvas>
      <Box className="axis-hint" aria-hidden="true">
        X → · Y ↗ · Z ↑
      </Box>
    </Box>
  )
}
