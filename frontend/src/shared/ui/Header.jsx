import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', position: 'relative' }} ref={menuRef}>
        <button 
          className="icon-button" 
          aria-label="Open navigation"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          ☰
        </button>
        <Link className="brand" to="/" onClick={() => setIsMenuOpen(false)}>
          <span className="brand-nom">Nom</span><span className="brand-pyr">pyr</span>
        </Link>
        
        {/* React Navigation Popup */}
        <div className={`popup-nav ${isMenuOpen ? '' : 'hidden'}`}>
          <div className="popup-nav-group-label" style={{fontSize:'0.65rem',fontWeight:800,letterSpacing:'0.1em',textTransform:'uppercase',color:'var(--accent)',padding:'0.5rem 0.75rem 0.25rem',opacity:0.7}}>🌊 Navigate</div>
          <Link to="/" className="popup-nav-item" onClick={() => setIsMenuOpen(false)}>⌂<span>Home</span></Link>
          <Link to="/search" className="popup-nav-item" onClick={() => setIsMenuOpen(false)}>⌕<span>Sonar Search</span></Link>
          
          <div style={{height:'1px',background:'var(--border)',margin:'0.5rem 0.75rem'}}></div>
          <div className="popup-nav-group-label" style={{fontSize:'0.65rem',fontWeight:800,letterSpacing:'0.1em',textTransform:'uppercase',color:'var(--accent)',padding:'0.5rem 0.75rem 0.25rem',opacity:0.7}}>⚓ My Collection</div>
          <Link to="/favorites" className="popup-nav-item" onClick={() => setIsMenuOpen(false)}>♡<span>Favorites</span></Link>
          <Link to="/history" className="popup-nav-item" onClick={() => setIsMenuOpen(false)}>↺<span>History</span></Link>
        </div>
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
