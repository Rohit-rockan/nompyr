import React from 'react';
import { useStore } from '@/shared/store/StoreContext';
import { AnimeCard } from '@/entities/anime/ui/AnimeCard';

export const HistoryPage = () => {
  const { history, clearHistory } = useStore();

  return (
    <main className="page-content">
      <section className="search-header" style={{ padding: '2rem 0', textAlign: 'center' }}>
        <h1 style={{ marginBottom: '1rem' }}>Watch History</h1>
        <p style={{ opacity: 0.7 }}>Resume where you left off.</p>
        
        {history.length > 0 && (
          <button 
            className="mini-action" 
            onClick={clearHistory}
            style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: 'rgba(255,0,0,0.2)', color: '#ff4d4d' }}
          >
            Clear History
          </button>
        )}
      </section>

      <section className="history-results">
        {history.length === 0 && (
          <div className="empty-message" style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>No history found.</h2>
            <p style={{ opacity: 0.7 }}>Watch some anime to populate this list!</p>
          </div>
        )}

        {history.length > 0 && (
          <div className="grid-layout" style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', 
            gap: '1.5rem',
            padding: '1rem'
          }}>
            {history.map(anime => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
};
