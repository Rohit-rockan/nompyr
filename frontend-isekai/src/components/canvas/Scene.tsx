'use client';

import { Suspense, useRef } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { ScrollControls, Scroll, useScroll, Preload } from '@react-three/drei';
import AncientRuins from '../3d/AncientRuins';
import HeroText from '../ui/HeroText';
import FishSchool from '../3d/FishSchool';
import PostProcessingEffects from '../3d/PostProcessing';

function OceanEnvironment() {
  const { scene } = useThree();
  
  // Set up volumetric fog for the ocean depth
  // The fog will get darker and denser as we scroll down
  scene.fog = new THREE.FogExp2('#020813', 0.02);

  return (
    <>
      <ambientLight intensity={0.2} color="#4fb6ff" />
      <directionalLight position={[0, 10, 0]} intensity={1.5} color="#cce6ff" />
      {/* Background color of the deep sea */}
      <color attach="background" args={['#01050b']} />
      
      {/* 
        This is a placeholder for the water caustics and god rays. 
      */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 5, 0]}>
        <planeGeometry args={[1000, 1000]} />
        <meshBasicMaterial color="#0a2a4a" transparent opacity={0.1} side={THREE.DoubleSide} />
      </mesh>
    </>
  );
}

function DivingCamera() {
  const scroll = useScroll();
  const { camera } = useThree();
  const startY = 5;
  const endY = -150; // Deep down into the abyss

  useFrame(() => {
    // scroll.offset goes from 0 to 1 as we scroll down
    const targetY = THREE.MathUtils.lerp(startY, endY, scroll.offset);
    
    // Smooth camera movement using linear interpolation (spring physics feel)
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, targetY, 0.05);
    
    // Slight tilt upwards as we dive to look at things passing by
    const targetRotationX = THREE.MathUtils.lerp(0, Math.PI * 0.1, scroll.offset);
    camera.rotation.x = THREE.MathUtils.lerp(camera.rotation.x, targetRotationX, 0.05);
  });

  return null;
}

function FloatingParticles({ count = 1000 }) {
  const points = useRef<THREE.Points>(null);

  // Generate random positions for plankton/bubbles
  const particlesPosition = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    particlesPosition[i * 3] = (Math.random() - 0.5) * 40; // x
    particlesPosition[i * 3 + 1] = (Math.random() - 0.5) * 160 - 75; // y (spread deep)
    particlesPosition[i * 3 + 2] = (Math.random() - 0.5) * 40; // z
  }

  useFrame((state) => {
    if (points.current) {
      points.current.rotation.y = state.clock.elapsedTime * 0.02;
      points.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    }
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[particlesPosition, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#88ccff"
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

// Imported components below

export default function Scene() {
  return (
    <div id="canvas-container">
      <Canvas camera={{ position: [0, 5, 10], fov: 45 }}>
        <Suspense fallback={null}>
          <OceanEnvironment />
          
          <ScrollControls pages={8} damping={0.2}>
            <DivingCamera />
            
            <Scroll>
              {/* 3D World Contents */}
              <FloatingParticles count={3000} />
              
              {/* Markers for different depth zones */}
              <AncientRuins position={[0, -20, -10]} title="Twilight Zone" />
              <AncientRuins position={[0, -60, -15]} title="Midnight Zone" />
              <AncientRuins position={[0, -110, -8]} title="The Abyss" />
              
              {/* Fish Schools */}
              <FishSchool position={[0, -5, -5]} count={150} color="#00ffcc" bounds={30} />
              <FishSchool position={[15, -40, -20]} count={200} color="#66b3ff" bounds={50} />
              <FishSchool position={[-10, -90, -10]} count={50} color="#9933ff" bounds={20} />
            </Scroll>
            
            <Scroll html style={{ width: '100%' }}>
              {/* 
                HTML Overlays mapped to scroll position.
                This is where we will put the Next.js UI elements, 
                like the Anime titles assembling from particles.
              */}
              <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <HeroText />
              </div>
              <div style={{ height: '100vh' }}></div>
              <div style={{ height: '100vh', padding: '10vw' }}>
                <p className="text-blue-100/50 mt-4 max-w-md text-2xl font-light">Every forgotten world sinks beneath time...</p>
              </div>
              <div style={{ height: '200vh' }}></div>
              <div style={{ height: '100vh', padding: '10vw', textAlign: 'right' }}>
                <p className="text-purple-100/50 mt-4 text-2xl font-light">Ancient ruins wait for those willing to dive.</p>
              </div>
            </Scroll>
            
          </ScrollControls>
          <PostProcessingEffects />
          <Preload all />
        </Suspense>
      </Canvas>
    </div>
  );
}
