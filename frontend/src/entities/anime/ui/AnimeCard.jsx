import React from 'react';
import { useStore } from '@/shared/store/StoreContext';

export const AnimeCard = ({ anime, compact = false }) => {
  const { favorites, toggleFavorite } = useStore();
  const isFavorite = favorites.includes(anime.id);

  const isFallback = String(anime.id).startsWith("search-fallback:");
  const isHanime = String(anime.id).startsWith("hanime:");
  
  const targetHash = isHanime 
    ? `https://hanime.tv/videos/hentai/${anime.id.split("hanime:")[1]}` 
    : isFallback 
      ? `#/search?fallback=${encodeURIComponent(anime.id.split("search-fallback:")[1])}` 
      : `#/anime/${anime.id}`;
      
  const targetAttr = isHanime ? { target: "_blank", rel: "noopener noreferrer" } : {};
  const sub = anime.sub_episodes || anime.latestEpisode || 1;
  const hasDub = anime.language && anime.language.join("/").toLowerCase().includes("dub");
  const dub = anime.dub_episodes || (hasDub ? anime.latestEpisode : 0) || 0;

  return (
    <article 
      className={`anime-card ${compact ? "compact" : ""}`} 
      style={{
        "--card-color": anime.color || "#1a1a2e",
        "--card-accent": anime.accent || "#e94560"
      }}
    >
      <a href={targetHash} {...targetAttr} className="poster-wrap">
        <img 
          src={anime.poster} 
          alt={anime.title} 
          className="poster" 
          loading="lazy" 
        />
        <span className="score">{anime.score || "N/A"}</span>
      </a>
      
      <div className="card-body">
        <a href={targetHash} {...targetAttr} className="card-title">
          {anime.title}
        </a>
        <div className="card-meta">
          <span className="badge-cc">CC {sub}</span>
          {dub > 0 && (
            <span className="badge-dub">
              <i className="fas fa-microphone-alt"></i> {dub}
            </span>
          )}
          <span className="type-tag">{anime.type || "TV"}</span>
        </div>
        
        <button 
          className="mini-action" 
          onClick={(e) => {
            e.preventDefault();
            toggleFavorite(anime.id);
          }}
          aria-label="Toggle favorite"
        >
          {isFavorite ? "♥" : "♡"}
        </button>
      </div>
    </article>
  );
};
