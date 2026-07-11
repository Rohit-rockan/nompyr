'use client';

import React, { useRef, useState } from 'react';
import anime from 'animejs';

interface IntroSequenceProps {
  onComplete: () => void;
}
import { useAudio } from '@/hooks/useAudio';

export default function IntroSequence({ onComplete }: IntroSequenceProps) {
  const [hasStarted, setHasStarted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const lightRef = useRef<HTMLDivElement>(null);
  const { initAudio, playClick } = useAudio();

  const handleDive = () => {
    setHasStarted(true);
    initAudio();
    playClick();

    // Note: We don't have the actual audio files, so we simulate them 
    // by using the Web Audio API or just the visual representation.
    
    // Simulate the sequence described in prompt
    const tl = anime.timeline({
      easing: 'easeInOutQuad',
    });

    tl
      // 1. A single light appears above
      .add({
        targets: lightRef.current,
        opacity: [0, 1],
        scale: [0.1, 1],
        duration: 4000,
      })
      // 2. The user slowly falls (fade out the black overlay to reveal the ocean)
      .add({
        targets: containerRef.current,
        opacity: [1, 0],
        duration: 3000,
        delay: 1000, // Wait a second before falling
        complete: () => {
          onComplete(); // Tell parent component we are done
        }
      });
  };

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black"
    >
      {/* The single light appearing above */}
      <div 
        ref={lightRef}
        className="absolute top-[20%] left-1/2 -translate-x-1/2 w-32 h-32 rounded-full opacity-0"
        style={{
          background: 'radial-gradient(circle, rgba(100,200,255,1) 0%, rgba(0,0,0,0) 70%)',
          filter: 'blur(20px)',
          boxShadow: '0 0 100px 20px rgba(100, 200, 255, 0.4)'
        }}
      />

      {/* Initial Interaction Button */}
      {!hasStarted && (
        <button 
          onClick={handleDive}
          className="relative z-10 px-8 py-3 text-cyan-200 border border-cyan-800 rounded-full hover:bg-cyan-900/30 transition-all tracking-[0.3em] uppercase text-sm font-light shadow-[0_0_15px_rgba(0,100,200,0.5)]"
        >
          Enter the Abyss
        </button>
      )}
    </div>
  );
}
