'use client';

import React from 'react';
import { EffectComposer, Bloom, DepthOfField, ChromaticAberration, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import * as THREE from 'three';

export default function PostProcessingEffects() {
  return (
    <EffectComposer>
      <Bloom 
        luminanceThreshold={0.5} 
        luminanceSmoothing={0.9} 
        intensity={2.5} 
        mipmapBlur 
      />
      
      <DepthOfField 
        focusDistance={0.02} 
        focalLength={0.05} 
        bokehScale={4} 
        height={480} 
      />
      
      <ChromaticAberration 
        blendFunction={BlendFunction.NORMAL} 
        offset={new THREE.Vector2(0.002, 0.002)} 
      />

      <Vignette eskil={false} offset={0.1} darkness={1.1} />
    </EffectComposer>
  );
}
