import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { animeApi } from '@/shared/api/anime';
import { useStore } from '@/shared/store/StoreContext';
import { EpisodeList } from './EpisodeList';
import { VideoPlayer } from './VideoPlayer';

export const AnimeDetailsPage = () => {
  const { id } = useParams();
  const { addToHistory } = useStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeEpisode, setActiveEpisode] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        // The backend returns { success: true, data: { ... } }
        const response = await animeApi.getDetails(id);
        if (response.success) {
          setData(response.data);
          addToHistory(response.data);
        } else {
          setError(response.error || "Failed to load anime details");
        }
      } catch (err) {
        setError(err.message || "Network Error");
      } finally {
        setLoading(false);
      }
    };
    
    if (id) {
      fetchDetails();
    }
  }, [id]);

  if (loading) return <div className="loading-spinner">Loading {id}...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;
  if (!data) return null;

  return (
    <main className="page-content details-view">
      <div 
        className="details-backdrop" 
        style={{ 
          backgroundImage: `url(${data.banner || data.poster})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          height: '40vh',
          position: 'relative'
        }}
      >
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to top, var(--bg) 0%, transparent 100%)'
        }}></div>
      </div>
      
      <div className="details-content" style={{ padding: '2rem', display: 'flex', gap: '2rem', marginTop: '-10vh', position: 'relative', zIndex: 10 }}>
        <img 
          src={data.poster} 
          alt={data.title} 
          style={{ width: '250px', borderRadius: '12px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }} 
        />
        
        <div className="details-info">
          <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{data.title}</h1>
          <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            <span>{data.type}</span>
            <span>⭐ {data.score}</span>
            <span>{data.status}</span>
          </div>
          
          <p style={{ lineHeight: '1.6', color: 'var(--text-secondary)' }}>
            {data.description || "No description available."}
          </p>
          
          <div style={{ marginTop: '2rem' }}>
            <button 
              className="primary-btn" 
              style={{ padding: '0.75rem 2rem', fontSize: '1.1rem' }}
              onClick={() => {
                document.getElementById('watch-section')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              ▶ Watch Now
            </button>
          </div>
        </div>
      </div>
      
      {/* Player & Episodes Section */}
      <div id="watch-section" style={{ padding: '2rem', display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        <div className="player-section">
          <h2 style={{ marginBottom: '1rem' }}>
            {activeEpisode ? `Watching: Episode ${activeEpisode.number}` : 'Select an Episode'}
          </h2>
          <VideoPlayer episode={activeEpisode} />
        </div>
        
        <div className="episodes-section">
          <h2 style={{ marginBottom: '1rem' }}>Episodes</h2>
          <div style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            <EpisodeList animeId={id} onSelectEpisode={setActiveEpisode} />
          </div>
        </div>
      </div>
    </main>
  );
};
