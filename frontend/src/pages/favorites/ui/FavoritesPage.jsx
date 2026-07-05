import React, { useEffect, useState } from 'react';
import { useStore } from '@/shared/store/StoreContext';
import { animeApi } from '@/shared/api/anime';
import { AnimeCard } from '@/entities/anime/ui/AnimeCard';

export const FavoritesPage = () => {
  const { favorites } = useStore();
  const [animeList, setAnimeList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFavorites = async () => {
      if (!favorites || favorites.length === 0) {
        setAnimeList([]);
        return;
      }

      setLoading(true);
      setError(null);
      
      try {
        const promises = favorites.map(id => animeApi.getDetails(id));
        const results = await Promise.allSettled(promises);
        
        const loadedAnimes = results
          .filter(res => res.status === 'fulfilled' && res.value.success)
          .map(res => res.value.data);
          
        setAnimeList(loadedAnimes);
      } catch (err) {
        setError("Failed to load favorites.");
      } finally {
        setLoading(false);
      }
    };

    fetchFavorites();
  }, [favorites]);

  return (
    <main className="page-content">
      <section className="search-header" style={{ padding: '2rem 0', textAlign: 'center' }}>
        <h1 style={{ marginBottom: '1rem' }}>My Collection</h1>
        <p style={{ opacity: 0.7 }}>Anime saved to your Sonar array.</p>
      </section>

      <section className="favorites-results">
        {loading && <div className="loading-spinner">Decrypting signals...</div>}
        {error && <div className="error-message">Error: {error}</div>}
        
        {!loading && !error && animeList.length === 0 && (
          <div className="empty-message" style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>No favorites yet.</h2>
            <p style={{ opacity: 0.7 }}>Go to the Home page and click the heart icon on any anime!</p>
          </div>
        )}

        {!loading && !error && animeList.length > 0 && (
          <div className="grid-layout" style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', 
            gap: '1.5rem',
            padding: '1rem'
          }}>
            {animeList.map(anime => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
};
