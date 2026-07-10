'use client';

import React, { useEffect, useRef } from 'react';
import anime from 'animejs';

export default function HeroText() {
  const textRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!textRef.current) return;
    
    // Split text into individual letters for particle assembly effect
    const text = textRef.current.textContent || "NOMPYR";
    textRef.current.innerHTML = '';
    
    text.split('').forEach((char) => {
      const span = document.createElement('span');
      span.textContent = char;
      span.style.display = 'inline-block';
      span.style.opacity = '0';
      span.className = 'letter filter drop-shadow-[0_0_10px_rgba(100,200,255,0.8)]';
      textRef.current?.appendChild(span);
    });

    const letters = textRef.current.querySelectorAll('.letter');

    // Plankton assembly animation loop
    const animationLoop = () => {
      anime.timeline({ loop: false })
        .add({
          targets: letters,
          translateY: [() => anime.random(-100, 100), 0],
          translateX: [() => anime.random(-100, 100), 0],
          translateZ: [() => anime.random(-400, 400), 0],
          opacity: [0, 1],
          filter: ['blur(10px)', 'blur(0px)'],
          easing: "easeOutElastic(1, .5)",
          duration: 3000,
          delay: anime.stagger(100)
        })
        .add({
          // Fish swims through breaking it apart
          targets: letters,
          translateX: () => anime.random(-200, 200),
          translateY: () => anime.random(-200, 200),
          rotateZ: () => anime.random(-45, 45),
          opacity: 0,
          filter: ['blur(0px)', 'blur(20px)'],
          duration: 1500,
          easing: "easeInExpo",
          delay: 4000,
          complete: () => {
            // Loop it
            setTimeout(animationLoop, 1000);
          }
        });
    };

    animationLoop();
  }, []);

  return (
    <h1 
      ref={textRef} 
      className="text-7xl md:text-9xl font-bold text-cyan-100 opacity-90 mix-blend-screen tracking-[0.3em] uppercase"
      style={{ textShadow: '0 0 30px rgba(0, 255, 255, 0.5)' }}
    >
      Nompyr
    </h1>
  );
}
