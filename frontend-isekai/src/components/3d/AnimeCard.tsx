'use client';

import React, { useRef, useEffect } from 'react';
import { Html } from '@react-three/drei';
import anime from 'animejs';
import { AnimeData } from '@/data/mockAnime';

interface AnimeCardProps {
  position: [number, number, number];
  data: AnimeData;
  delay?: number;
}

export default function AnimeCard({ position, data, delay = 0 }: AnimeCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!cardRef.current) return;

    // Initial appearance animation (Rising from the sand)
    anime({
      targets: cardRef.current,
      translateY: [50, 0],
      opacity: [0, 1],
      scale: [0.8, 1],
      duration: 2000,
      delay: delay,
      easing: 'easeOutElastic(1, .5)',
    });

    // Wobble effect (ambient water current)
    anime({
      targets: cardRef.current,
      translateY: '-=5',
      rotateZ: [
        { value: 1, duration: 2000, easing: 'easeInOutSine' },
        { value: -1, duration: 2000, easing: 'easeInOutSine' }
      ],
      loop: true,
      direction: 'alternate',
    });
  }, [delay]);

  const handleMouseEnter = () => {
    if (!cardRef.current) return;
    anime({
      targets: cardRef.current,
      scale: 1.1,
      rotateX: 10,
      rotateY: 5,
      boxShadow: '0 0 30px rgba(100, 200, 255, 0.6)',
      duration: 800,
      easing: 'easeOutElastic(1, .5)',
    });
    
    // Animate "seaweed" overlay away
    const seaweed = cardRef.current.querySelector('.seaweed-overlay');
    if (seaweed) {
      anime({
        targets: seaweed,
        opacity: 0,
        translateY: 20,
        duration: 500,
        easing: 'easeOutQuad'
      });
    }
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    anime({
      targets: cardRef.current,
      scale: 1,
      rotateX: 0,
      rotateY: 0,
      boxShadow: '0 0 10px rgba(0, 0, 0, 0.5)',
      duration: 800,
      easing: 'easeOutElastic(1, .5)',
    });
    
    const seaweed = cardRef.current.querySelector('.seaweed-overlay');
    if (seaweed) {
      anime({
        targets: seaweed,
        opacity: 1,
        translateY: 0,
        duration: 500,
        easing: 'easeOutQuad'
      });
    }
  };

  const handleClick = () => {
    if (!cardRef.current) return;
    
    // Zoom into the card to "discover the world" before redirecting
    anime({
      targets: cardRef.current,
      scale: 10,
      opacity: 0,
      duration: 1500,
      easing: 'easeInExpo',
      complete: () => {
        // Redirect to the legacy app's watch page
        window.location.href = `http://127.0.0.1:8123/anineko_watch.html?v=${data.id}`;
      }
    });
  };

  return (
    <group position={position}>
      <Html transform center distanceFactor={15} zIndexRange={[100, 0]}>
        <div 
          ref={cardRef}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          className="relative w-48 h-72 rounded-xl overflow-hidden cursor-pointer bg-black border border-cyan-900/50 backdrop-blur-md"
          style={{ transformOrigin: 'center center', opacity: 0 }}
        >
          {/* Card Image */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img 
            src={data.imageUrl} 
            alt={data.title} 
            className="absolute inset-0 w-full h-full object-cover mix-blend-luminosity hover:mix-blend-normal transition-all duration-1000"
          />
          
          {/* Mock "Seaweed" / Sand Overlay */}
          <div className="seaweed-overlay absolute inset-0 bg-gradient-to-t from-green-900/80 via-black/50 to-transparent z-10" />
          
          {/* Info */}
          <div className="absolute bottom-0 left-0 w-full p-4 bg-gradient-to-t from-black via-black/80 to-transparent z-20">
            <p className="text-cyan-400 text-xs tracking-widest font-mono mb-1">{data.genre}</p>
            <h3 className="text-white text-lg font-bold leading-tight">{data.title}</h3>
          </div>
        </div>
      </Html>
    </group>
  );
}
