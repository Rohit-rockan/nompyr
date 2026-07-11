'use client';

import React from 'react';
import AnimeCard from './AnimeCard';
import { mockAnime } from '@/data/mockAnime';
import { Html } from '@react-three/drei';

interface AncientRuinsProps {
  position: [number, number, number];
  title: string;
}

export default function AncientRuins({ position, title }: AncientRuinsProps) {
  return (
    <group position={position}>
      {/* Ruins Base Structure (Placeholder using basic shapes) */}
      <mesh position={[0, -2, 0]}>
        <cylinderGeometry args={[15, 18, 2, 8]} />
        <meshStandardMaterial color="#0a1520" roughness={1} />
      </mesh>
      
      {/* Pillars */}
      <mesh position={[-10, 5, -5]}>
        <cylinderGeometry args={[0.5, 0.5, 14, 8]} />
        <meshStandardMaterial color="#0a1520" roughness={0.9} />
      </mesh>
      <mesh position={[10, 2, -2]}>
        <cylinderGeometry args={[0.5, 0.5, 8, 8]} />
        <meshStandardMaterial color="#0a1520" roughness={0.9} />
      </mesh>
      
      {/* Ruins Title Overlay */}
      <Html position={[0, 8, 0]} transform center distanceFactor={20}>
        <div className="text-cyan-600/30 text-6xl font-mono uppercase tracking-[0.5em] pointer-events-none whitespace-nowrap">
          {title}
        </div>
      </Html>

      {/* Anime Cards scattered on the ruins */}
      <AnimeCard position={[-5, 2, 2]} data={mockAnime[0]} delay={0} />
      <AnimeCard position={[0, 1, 4]} data={mockAnime[1]} delay={200} />
      <AnimeCard position={[5, 3, 1]} data={mockAnime[2]} delay={400} />
    </group>
  );
}
