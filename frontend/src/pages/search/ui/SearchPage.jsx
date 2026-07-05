import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { searchApi } from '@/shared/api/search';
import { AnimeCard } from '@/entities/anime/ui/AnimeCard';

export const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Hook into URL query params
  const location = useLocation();
  const navigate = useNavigate();
  
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get('q');
    if (q) {
      setQuery(q);
      executeSearch(q);
    }
  }, [location.search]);

  const executeSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;
    try {
      setLoading(true);
      setError(null);
      setHasSearched(true);
      
      const response = await searchApi.searchAnime(searchQuery);
      if (response.success) {
        setResults(response.data || []);
      } else {
        setError(response.error || "Search failed.");
      }
    } catch (err) {
      setError(err.message || "Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      // Update URL which will trigger the useEffect
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <main className="page-content">
      <section className="search-header" style={{ padding: '2rem 0', textAlign: 'center' }}>
        <h1 style={{ marginBottom: '1rem' }}>Explore The Depths</h1>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', maxWidth: '600px', margin: '0 auto' }}>
          <input 
            type="search" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search anime..." 
            style={{ 
              padding: '1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border)', 
              background: 'var(--bg-lighter)',
              color: 'var(--text)',
              flex: 1,
              fontSize: '1.1rem'
            }} 
          />
          <button type="submit" className="primary-btn" style={{ padding: '0 2rem' }}>DIVE</button>
        </form>
      </section>

      <section className="search-results">
        {loading && <div className="loading-spinner">Scanning frequencies...</div>}
        {error && <div className="error-message">Error: {error}</div>}
        
        {!loading && !error && hasSearched && results.length === 0 && (
          <div className="empty-message" style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>No signals found.</h2>
            <p style={{ opacity: 0.7 }}>Try adjusting your search query.</p>
          </div>
        )}

        {!loading && !error && results.length > 0 && (
          <div className="grid-layout" style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', 
            gap: '1.5rem',
            padding: '1rem'
          }}>
            {results.map(anime => (
              <AnimeCard key={anime.id} anime={anime} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
};
