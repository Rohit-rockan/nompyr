import { useContext } from 'react';
import { AudioContext } from '../components/audio/AudioManager';

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider');
  }
  return context;
};
