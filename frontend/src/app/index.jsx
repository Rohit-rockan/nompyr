import React from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { HomePage } from '@/pages/home/ui/HomePage';
import { AnimeDetailsPage } from '@/pages/details/ui/AnimeDetailsPage';
import { SearchPage } from '@/pages/search/ui/SearchPage';
import { FavoritesPage } from '@/pages/favorites/ui/FavoritesPage';
import { HistoryPage } from '@/pages/history/ui/HistoryPage';
import { Header } from '@/shared/ui/Header';
import { StoreProvider } from '@/shared/store/StoreContext';

const App = () => {
  return (
    <StoreProvider>
      <HashRouter>
        <Header />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/anime/:id" element={<AnimeDetailsPage />} />
          {/* We can add more routes here as we migrate them */}
        </Routes>
      </HashRouter>
    </StoreProvider>
  );
};

export const initReactApp = () => {
  const rootElement = document.getElementById('react-root');
  if (rootElement) {
    // Hide legacy Vanilla JS UI elements
    const legacyView = document.getElementById('view');
    if (legacyView) legacyView.style.display = 'none';
    
    const legacyTopbar = document.querySelector('header.topbar');
    if (legacyTopbar) legacyTopbar.style.display = 'none';

    const root = createRoot(rootElement);
    root.render(<App />);
  }
};
