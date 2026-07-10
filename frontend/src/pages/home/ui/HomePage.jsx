import React, { useEffect, useState } from 'react';
import { homeApi } from '@/shared/api/home';
import { AnimeCard } from '@/entities/anime/ui/AnimeCard';

export const HomePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHome = async () => {
      try {
        setLoading(true);
        const response = await homeApi.getHomeFeed();
        if (response.success) {
          setData(response.data);
        } else {
          setError("Failed to load home feed");
        }
      } catch (err) {
        setError(err.message || "Network Error");
      } finally {
        setLoading(false);
      }
    };
    fetchHome();
  }, []);

  if (loading) return <div className="loading-spinner">Loading Nompyr...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;
  if (!data) return null;

  return (
    <main className="page-content">
      {/* Hero Section */}
      {data.trending && data.trending.length > 0 && (
        <section className="hero-banner">
          <img src={data.trending[0].poster} alt="Trending" className="hero-backdrop" />
          <div className="hero-overlay"></div>
          <div className="hero-content">
            <div className="hero-badge">FEATURED</div>
            <h1>{data.trending[0].title}</h1>
            
            <div className="hero-tags">
              <span>{data.trending[0].type || 'TV'}</span>
              <span>{data.trending[0].status || 'HD'}</span>
              <span>Sub/Dub</span>
            </div>
            
            <p className="hero-description">{data.trending[0].description || "Trending now on Nompyr!"}</p>
            
            <div className="hero-meta-grid">
               <div><strong>Genres:</strong> Action, Adventure, Fantasy</div>
               <div><strong>Studio:</strong> Animation Studio</div>
            </div>

            <div className="hero-actions">
                <a href={`#/anime/${data.trending[0].id}`} className="hero-btn primary-btn">
                  Watch Now
                </a>
                <a href={`#/anime/${data.trending[0].id}`} className="hero-btn secondary-btn">
                  View Details
                </a>
            </div>
          </div>
        </section>
      )}

      {/* Content Rows */}
      {data.recent && data.recent.length > 0 && (
        <section className="content-row">
          <div className="section-head">
            <h2>Recently Updated</h2>
          </div>
          <div className="card-scroller">
            {data.recent.map(anime => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>
        </section>
      )}

      {data.topAiring && data.topAiring.length > 0 && (
        <section className="content-row">
          <div className="section-head">
            <h2>Top Airing</h2>
          </div>
          <div className="card-scroller">
            {data.topAiring.map(anime => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
};
