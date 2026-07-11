'use client';

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface FishSchoolProps {
  count?: number;
  color?: string;
  position?: [number, number, number];
  bounds?: number;
}

export default function FishSchool({ 
  count = 100, 
  color = '#4faacc',
  position = [0, 0, 0],
  bounds = 20
}: FishSchoolProps) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  
  // Create dummy object to compute matrix for each instance
  const dummy = useMemo(() => new THREE.Object3D(), []);

  // Initialize random positions, phases, and speeds for the fish
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      const x = (Math.random() - 0.5) * bounds;
      const y = (Math.random() - 0.5) * bounds;
      const z = (Math.random() - 0.5) * bounds;
      
      const speed = 0.5 + Math.random() * 2;
      const phase = Math.random() * Math.PI * 2;
      
      temp.push({ x, y, z, speed, phase });
    }
    return temp;
  }, [count, bounds]);

  useFrame((state) => {
    if (!meshRef.current) return;
    
    const time = state.clock.elapsedTime;
    
    particles.forEach((particle, i) => {
      // Simulate swimming motion (sine wave along X/Z axis)
      const moveZ = Math.sin(time * particle.speed + particle.phase) * 0.05;
      const moveX = Math.cos(time * particle.speed + particle.phase) * 0.05;
      const moveY = Math.sin(time * particle.speed * 0.5 + particle.phase) * 0.02;
      
      particle.x += moveX;
      particle.y += moveY;
      particle.z += moveZ;

      // Keep them within bounds
      if (particle.x > bounds / 2) particle.x = -bounds / 2;
      if (particle.x < -bounds / 2) particle.x = bounds / 2;
      if (particle.z > bounds / 2) particle.z = -bounds / 2;
      if (particle.z < -bounds / 2) particle.z = bounds / 2;
      if (particle.y > bounds / 2) particle.y = -bounds / 2;
      if (particle.y < -bounds / 2) particle.y = bounds / 2;

      // Update position
      dummy.position.set(particle.x, particle.y, particle.z);
      
      // Calculate rotation to face direction of movement
      const targetRotation = Math.atan2(moveX, moveZ);
      dummy.rotation.y = targetRotation;
      
      // Add slight "wobble" for fish tail swimming
      dummy.rotation.x = moveY * 2;
      dummy.rotation.z = Math.sin(time * particle.speed * 5) * 0.1;

      dummy.updateMatrix();
      meshRef.current!.setMatrixAt(i, dummy.matrix);
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <group position={position}>
      <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
        {/* A simple cone shape representing a fish/squid */}
        <coneGeometry args={[0.1, 0.4, 4]} />
        <meshStandardMaterial 
          color={color} 
          roughness={0.2} 
          metalness={0.8} 
          emissive={color}
          emissiveIntensity={0.2}
        />
      </instancedMesh>
    </group>
  );
}
