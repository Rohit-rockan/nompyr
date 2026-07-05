import React, { useEffect, useRef, useState } from 'react';
import { animeApi } from '@/shared/api/anime';

export const VideoPlayer = ({ episode }) => {
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sources, setSources] = useState(null);

  useEffect(() => {
    const fetchSources = async () => {
      if (!episode) return;
      try {
        setLoading(true);
        setError(null);
        const response = await animeApi.getSources(episode.id);
        if (response.success && response.sources && response.sources.length > 0) {
          setSources(response.sources);
          initializePlayer(response.sources[0].url); // Autoplay first source
        } else {
          setError(response.error || "No sources found for this episode.");
        }
      } catch (err) {
        setError(err.message || "Failed to fetch sources.");
      } finally {
        setLoading(false);
      }
    };

    fetchSources();
  }, [episode]);

  const initializePlayer = (url) => {
    const video = videoRef.current;
    if (!video) return;

    if (window.Hls && window.Hls.isSupported()) {
      const hls = new window.Hls();
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(e => console.log("Autoplay prevented:", e));
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        video.play().catch(e => console.log("Autoplay prevented:", e));
      });
    }
  };

  if (!episode) {
    return <div className="video-placeholder">Select an episode to start watching</div>;
  }

  return (
    <div className="video-container" style={{ width: '100%', aspectRatio: '16/9', background: '#000', position: 'relative', borderRadius: '12px', overflow: 'hidden' }}>
      {loading && <div className="loading-overlay" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'rgba(0,0,0,0.5)', color: '#fff', zIndex: 10 }}>Fetching Sources...</div>}
      {error && <div className="error-overlay" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'rgba(0,0,0,0.8)', color: 'var(--accent)', zIndex: 10 }}>{error}</div>}
      
      <video 
        ref={videoRef}
        controls 
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
