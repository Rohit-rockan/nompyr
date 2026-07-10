'use client';

import { useState, useEffect } from 'react';
import Scene from '@/components/canvas/Scene';
import DepthMeter from '@/components/ui/DepthMeter';
import IntroSequence from '@/components/ui/IntroSequence';

export default function Home() {
  const [introFinished, setIntroFinished] = useState(false);
  // We'll track depth as a percentage of scroll progress
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    // Drei's ScrollControls creates a wrapper div. We can track its scroll.
    const handleScroll = () => {
      // Find the scroll container created by Drei
      // It typically has absolute positioning and overflow-y auto
      const scrollContainers = document.querySelectorAll('div[style*="overflow-y: auto"]');
      if (scrollContainers.length > 0) {
        const container = scrollContainers[0] as HTMLElement;
        const maxScroll = container.scrollHeight - container.clientHeight;
        const progress = Math.min(Math.max(container.scrollTop / maxScroll, 0), 1);
        setScrollProgress(progress);
      }
    };

    // We'll run an animation frame loop to poll for scroll changes
    // since the Drei container is generated dynamically
    let animationFrameId: number;
    const loop = () => {
      handleScroll();
      animationFrameId = requestAnimationFrame(loop);
    };
    loop();

    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return (
    <main className="relative w-full h-screen overflow-hidden bg-black text-white selection:bg-cyan-500/30">
      {!introFinished && <IntroSequence onComplete={() => setIntroFinished(true)} />}
      
      {/* 
        We render the Scene and DepthMeter even if intro is running, 
        but they sit behind the black IntroSequence overlay. 
      */}
      <Scene />
      <DepthMeter progress={scrollProgress} />
      
      {/* 
        This is a UI overlay layer. Additional overlays like a global navigation 
        or audio controls can go here.
      */}
      <div className="fixed top-8 left-8 z-50 pointer-events-none">
        <h1 className="text-xl font-mono tracking-widest text-cyan-50/50">NOMPYR</h1>
      </div>
    </main>
  );
}
