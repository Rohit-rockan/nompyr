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
          <div className="hero-content">
            <h1>{data.trending[0].title}</h1>
            <p className="hero-description">{data.trending[0].description || "Trending now on Nompyr!"}</p>
            <a href={`#/anime/${data.trending[0].id}`} className="primary-btn">
              ▶ Watch Now
            </a>
          </div>
          <img src={data.trending[0].poster} alt="Trending" className="hero-backdrop" />
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
