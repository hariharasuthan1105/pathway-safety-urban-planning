import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CitySceneProps {
  riskScore?: number;
  riskLevel?: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

const BuildingMeshGroup: React.FC<{ targetColor: string }> = ({ targetColor }) => {
  const groupRef = useRef<THREE.Group>(null);

  // Generate 32 building mesh coordinates
  const buildings = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 32; i++) {
      const angle = (i / 32) * Math.PI * 2;
      const radius = 3 + (i % 5) * 2.5;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const h = 2 + (i % 4) * 2.2;
      const w = 1.2 + (i % 3) * 0.4;
      arr.push({ x, z, h, w });
    }
    return arr;
  }, []);

  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = clock.getElapsedTime() * 0.05;
    }
  });

  return (
    <group ref={groupRef}>
      {buildings.map((b, idx) => (
        <mesh key={idx} position={[b.x, b.h / 2, b.z]}>
          <boxGeometry args={[b.w, b.h, b.w]} />
          <meshPhongMaterial
            color="#0F172A"
            emissive={idx % 3 === 0 ? targetColor : '#1E293B'}
            specular="#3B82F6"
            shininess={30}
            transparent
            opacity={0.85}
          />
        </mesh>
      ))}
      <gridHelper args={[36, 24, '#3B82F6', '#1E293B']} position={[0, -0.05, 0]} />
    </group>
  );
};

export const CitySceneContent: React.FC<CitySceneProps> = ({
  riskScore = 0,
  riskLevel = 'LOW',
}) => {
  const targetColor =
    riskScore > 75 || riskLevel === 'CRITICAL' ? '#EF4444' :
    riskScore > 50 || riskLevel === 'HIGH' ? '#F97316' :
    riskScore > 25 || riskLevel === 'MODERATE' ? '#F5B301' : '#10B981';

  return (
    <div className="relative w-full h-[280px] rounded-2xl overflow-hidden glass-surface">
      <Canvas
        camera={{ position: [0, 16, 28], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
      >
        <color attach="background" args={['#04070D']} />
        <fogExp2 attach="fog" args={['#04070D', 0.035]} />
        <ambientLight intensity={1.5} color="#1E293B" />
        <directionalLight position={[10, 20, 15]} intensity={2.0} color="#3B82F6" />
        <pointLight position={[0, 10, 0]} intensity={3.0} color="#06B6D4" />
        <BuildingMeshGroup targetColor={targetColor} />
      </Canvas>

      <div className="absolute bottom-3 left-3 px-3 py-1 rounded-full text-xs font-semibold glass-surface text-white flex items-center gap-2 border border-slate-700">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: targetColor }} />
        <span>Live Illumination: Risk {riskScore}/100 ({riskLevel})</span>
      </div>
    </div>
  );
};

export default CitySceneContent;
