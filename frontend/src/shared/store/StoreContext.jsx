import React, { createContext, useContext, useState, useEffect } from 'react';

const StoreContext = createContext();

export const useStore = () => useContext(StoreContext);

export const StoreProvider = ({ children }) => {
  const [favorites, setFavorites] = useState([]);
  const [history, setHistory] = useState([]);

  // Load initial state from legacy localStorage keys to remain compatible
  useEffect(() => {
    try {
      const favs = JSON.parse(localStorage.getItem('nompyr_favorites') || '[]');
      const hist = JSON.parse(localStorage.getItem('nompyr_history') || '[]');
      setFavorites(favs);
      setHistory(hist);
    } catch (e) {
      console.warn("Failed to load local storage state", e);
    }
  }, []);

  const toggleFavorite = (animeId) => {
    setFavorites(prev => {
      const updated = prev.includes(animeId) 
        ? prev.filter(id => id !== animeId)
        : [...prev, animeId];
      localStorage.setItem('nompyr_favorites', JSON.stringify(updated));
      return updated;
    });
  };

  const addToHistory = (animeObj) => {
    setHistory(prev => {
      // Remove if exists to push to front
      const filtered = prev.filter(item => item.id !== animeObj.id);
      const updated = [animeObj, ...filtered].slice(0, 50); // Keep last 50
      localStorage.setItem('nompyr_history', JSON.stringify(updated));
      return updated;
    });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('nompyr_history');
  };

  return (
    <StoreContext.Provider value={{ favorites, history, toggleFavorite, addToHistory, clearHistory }}>
      {children}
    </StoreContext.Provider>
  );
};
