import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', position: 'relative' }}>
        <button className="icon-button" aria-label="Open navigation">☰</button>
        <Link className="brand" to="/">
          <span className="brand-nom">Nom</span><span className="brand-pyr">pyr</span>
        </Link>
      </div>

      <form className="searchbar" onSubmit={handleSearch}>
        <div className="search-input-wrap" style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
          <input 
            type="search" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Sonar search anime..." 
            autoComplete="off" 
            style={{ width: '100%' }} 
          />
        </div>
        <button type="submit" className="search-submit-btn">DIVE</button>
      </form>

      <div className="topbar-actions">
        <button type="button" className="icon-button" title="Random Anime">⇆</button>
        <div className="theme-toggle-wrap">
          <button type="button" className="theme-btn">DEEP</button>
          <button type="button" className="theme-btn">SURFACE</button>
        </div>
        <Link className="profile-chip" to="/profile" style={{ padding: 0, width: '2.65rem', height: '2.65rem', borderRadius: '50%', overflow: 'hidden', display: 'grid', placeItems: 'center' }}>
          <span className="avatar" style={{ width: '100%', height: '100%', borderRadius: 0, fontSize: '0.75rem' }}>AK</span>
        </Link>
      </div>
    </header>
  );
};
