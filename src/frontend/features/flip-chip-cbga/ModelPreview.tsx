import {
  Bounds,
  Edges,
  GizmoHelper,
  GizmoViewport,
  OrbitControls,
} from '@react-three/drei'
import { Canvas, type ThreeEvent } from '@react-three/fiber'
import { Box, Typography } from '@mui/material'

import { toNativeXyzBlockTransform } from './previewGeometry'
import type { AxisAlignedBlock, Material, PackageModel } from './types'

interface ModelPreviewProps {
  model: PackageModel | null
  selectedBlockId: string | null
  hiddenBlockIds: ReadonlySet<string>
  onSelectBlock: (blockId: string | null) => void
}

interface PackageBlockProps {
  block: AxisAlignedBlock
  material: Material | undefined
  selected: boolean
  onSelect: (blockId: string) => void
}

const translucentStructures = new Set(['underfill', 'static_air', 'encapsulant'])

function PackageBlock({ block, material, selected, onSelect }: PackageBlockProps) {
  const { position, size } = toNativeXyzBlockTransform(block)
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
  hiddenBlockIds,
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
  const visibleBlocks = model.blocks.filter((block) => !hiddenBlockIds.has(block.id))

  return (
    <Box className="model-canvas" aria-label="Flip Chip CBGA 三维模型">
      <Canvas
        camera={{
          position: [8, -9, 6.5],
          up: [0, 0, 1],
          fov: 38,
          near: 0.01,
          far: 1000,
        }}
        onPointerMissed={() => onSelectBlock(null)}
      >
        <color attach="background" args={['#f7fafb']} />
        <ambientLight intensity={1.15} />
        <directionalLight position={[5, -7, 10]} intensity={1.8} />
        <directionalLight position={[-5, 4, 2]} intensity={0.6} />
        {visibleBlocks.length > 0 && (
          <Bounds fit clip observe margin={1.22}>
            {visibleBlocks.map((block) => (
              <PackageBlock
                key={block.id}
                block={block}
                material={materials.get(block.material_id)}
                selected={block.id === selectedBlockId}
                onSelect={onSelectBlock}
              />
            ))}
          </Bounds>
        )}
        <OrbitControls makeDefault enableDamping />
        <GizmoHelper alignment="bottom-right" margin={[72, 72]}>
          <GizmoViewport
            axisColors={['#e53935', '#43a047', '#1e88e5']}
            labels={['X', 'Y', 'Z']}
            labelColor="#ffffff"
            axisHeadScale={1.05}
            hideNegativeAxes
          />
        </GizmoHelper>
      </Canvas>
      {visibleBlocks.length === 0 && (
        <Box className="preview-visibility-note">所有模型均已隐藏</Box>
      )}
    </Box>
  )
}
