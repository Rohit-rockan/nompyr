'use client';

import React, { createContext, useEffect, useRef, useState } from 'react';
import { Howl, Howler } from 'howler';

interface AudioContextType {
  initAudio: () => void;
  playHover: () => void;
  playClick: () => void;
  playGateSwell: () => void;
  isMuted: boolean;
  toggleMute: () => void;
  setScrollDepth: (depth: number) => void;
}

export const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const AudioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  // Background layers
  const baseAmbience = useRef<Howl | null>(null);
  const rumble = useRef<Howl | null>(null);

  // SFX
  const hoverSfx = useRef<Howl | null>(null);
  const clickSfx = useRef<Howl | null>(null);
  const gateSwell = useRef<Howl | null>(null);

  useEffect(() => {
    // Initialize Howls but don't play yet
    baseAmbience.current = new Howl({
      src: ['/audio/base_ambience.mp3'], 
      loop: true,
      volume: 0.5,
      html5: true, // Use HTML5 audio for large streams
    });

    rumble.current = new Howl({
      src: ['/audio/rumble.mp3'],
      loop: true,
      volume: 0, // Starts at 0, increases on scroll
      html5: true,
    });

    hoverSfx.current = new Howl({
      src: ['/audio/hover_sparkle.mp3'],
      volume: 0.3,
    });

    clickSfx.current = new Howl({
      src: ['/audio/click_ripple.mp3'],
      volume: 0.5,
    });

    gateSwell.current = new Howl({
      src: ['/audio/gate_swell.mp3'],
      volume: 0.8,
    });

    return () => {
      // Cleanup on unmount
      baseAmbience.current?.unload();
      rumble.current?.unload();
      hoverSfx.current?.unload();
      clickSfx.current?.unload();
      gateSwell.current?.unload();
    };
  }, []);

  const initAudio = () => {
    if (!isInitialized) {
      baseAmbience.current?.play();
      rumble.current?.play();
      setIsInitialized(true);
    }
  };

  const playHover = () => hoverSfx.current?.play();
  const playClick = () => clickSfx.current?.play();
  const playGateSwell = () => gateSwell.current?.play();

  const toggleMute = () => {
    Howler.mute(!isMuted);
    setIsMuted(!isMuted);
  };

  const setScrollDepth = (depth: number) => {
    // Map depth (0 to 1) to volume (0 to 1) for the rumble track
    if (rumble.current) {
      const volume = Math.min(Math.max(depth, 0), 1) * 0.8; // Cap at 80% volume
      rumble.current.volume(volume);
    }
  };

  return (
    <AudioContext.Provider
      value={{
        initAudio,
        playHover,
        playClick,
        playGateSwell,
        isMuted,
        toggleMute,
        setScrollDepth,
      }}
    >
      {children}
    </AudioContext.Provider>
  );
};
