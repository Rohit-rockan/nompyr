import React, { useEffect, useState } from 'react';
import { animeApi } from '@/shared/api/anime';

export const EpisodeList = ({ animeId, onSelectEpisode }) => {
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeEpisodeId, setActiveEpisodeId] = useState(null);

  useEffect(() => {
    const fetchEpisodes = async () => {
      try {
        setLoading(true);
        const response = await animeApi.getEpisodes(animeId);
        if (response.success) {
          setEpisodes(response.data || response.episodes || []);
        } else {
          setError(response.error || "Failed to load episodes");
        }
      } catch (err) {
        setError(err.message || "Network Error");
      } finally {
        setLoading(false);
      }
    };
    
    if (animeId) {
      fetchEpisodes();
    }
  }, [animeId]);

  const handleSelect = (ep) => {
    setActiveEpisodeId(ep.id);
    if (onSelectEpisode) {
      onSelectEpisode(ep);
    }
  };

  if (loading) return <div className="loading-spinner">Loading Episodes...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;
  if (episodes.length === 0) return <div className="empty-message">No episodes available.</div>;

  return (
    <div className="episode-list">
      {episodes.map(ep => (
        <button
          key={ep.id}
          className={`episode-btn ${activeEpisodeId === ep.id ? 'active' : ''} ${ep.isFiller ? 'filler' : ''}`}
          onClick={() => handleSelect(ep)}
          style={{
            padding: '0.75rem 1rem',
            background: activeEpisodeId === ep.id ? 'var(--accent)' : 'var(--bg-lighter)',
            color: activeEpisodeId === ep.id ? '#fff' : 'var(--text)',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            textAlign: 'left',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.25rem'
          }}
        >
          <span style={{ fontWeight: 'bold' }}>Episode {ep.number}</span>
          {ep.title && <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>{ep.title}</span>}
        </button>
      ))}
    </div>
  );
};
