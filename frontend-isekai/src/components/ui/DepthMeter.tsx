'use client';

import React from 'react';

interface DepthMeterProps {
  progress: number; // 0 to 1
}

export default function DepthMeter({ progress }: DepthMeterProps) {
  // Convert progress (0 to 1) into a depth in meters (0 to 1000+)
  const maxDepth = 11000; // Marianas Trench depth
  const currentDepth = Math.floor(progress * maxDepth);
  
  // Determine zone name based on depth
  let zoneName = "Surface";
  let zoneColor = "text-cyan-200";
  
  if (currentDepth > 8000) {
    zoneName = "Abyss";
    zoneColor = "text-purple-600";
  } else if (currentDepth > 4000) {
    zoneName = "Midnight Zone";
    zoneColor = "text-blue-800";
  } else if (currentDepth > 1000) {
    zoneName = "Twilight Zone";
    zoneColor = "text-blue-500";
  } else if (currentDepth > 200) {
    zoneName = "Epipelagic";
    zoneColor = "text-cyan-400";
  }

  return (
    <div className="fixed right-8 top-1/2 -translate-y-1/2 flex flex-col items-end z-50 pointer-events-none select-none mix-blend-screen opacity-70">
      <div className={`text-sm font-mono tracking-[0.2em] uppercase mb-2 transition-colors duration-1000 ${zoneColor}`}>
        {zoneName}
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="text-3xl font-light font-mono tabular-nums leading-none">
            {currentDepth.toLocaleString()}
          </div>
          <div className="text-xs text-white/50 tracking-widest mt-1">METERS</div>
        </div>
        
        {/* The visual meter line */}
        <div className="relative w-[2px] h-32 bg-white/10 rounded-full overflow-hidden">
          <div 
            className="absolute top-0 left-0 w-full bg-gradient-to-b from-cyan-300 via-blue-500 to-purple-600 rounded-full transition-transform duration-75"
            style={{ 
              height: '100%',
              transform: `translateY(${-100 + (progress * 100)}%)` 
            }}
          />
        </div>
      </div>
    </div>
  );
}
