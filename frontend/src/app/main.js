import { animeCatalog } from "../data/anime.js?v=4";
import { sourceManager, normalizeAnime, mapJikanToNompyr } from "../services/sourceManager.js?v=4";
import { store } from "../services/store.js?v=4";

const view = document.querySelector("#view");
const navLinks = [...document.querySelectorAll("[data-nav]")];
const toast = document.querySelector("#toast");
const globalSearch = document.querySelector("#globalSearch");
const searchInput = document.querySelector("#searchInput");
const menuToggle = document.querySelector("#menuToggle");
const rail = document.querySelector(".rail") || { classList: { remove: () => {}, toggle: () => {}, contains: () => false } };

const state = {
  heroIndex: 0,
  filters: {},
  activeServerId: null,
  activeLanguage: null,
  currentEpisodeId: null,
  videoHlsInstance: null,
  watchdog: null
};

const formatTime = (seconds) => {
  if (isNaN(seconds)) return "00:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${m}:${String(s).padStart(2, '0')}`;
};

const handleKeyboardShortcuts = (event) => {
  const video = document.getElementById("videoPlayer");
  if (!video) return;

  if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA" || document.activeElement.tagName === "SELECT") {
    return;
  }

  const key = event.key.toLowerCase();
  if (key === " ") {
    event.preventDefault();
    if (video.paused) video.play().catch(() => {});
    else video.pause();
  } else if (key === "f") {
    event.preventDefault();
    if (!document.fullscreenElement) {
      video.requestFullscreen?.() || video.webkitRequestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  } else if (key === "t") {
    event.preventDefault();
    const player = document.querySelector(".player");
    if (player) {
      const isTheatreNow = !player.classList.contains("theatre");
      player.classList.toggle("theatre", isTheatreNow);
      store.updateSetting("theatre", isTheatreNow);
      showToast(isTheatreNow ? "Theatre mode enabled" : "Theatre mode disabled");
    }
  } else if (key === "m") {
    event.preventDefault();
    video.muted = !video.muted;
    showToast(video.muted ? "Muted" : "Unmuted");
  } else if (key === "arrowright") {
    event.preventDefault();
    video.currentTime = Math.min(video.duration || 0, video.currentTime + 10);
  } else if (key === "arrowleft") {
    event.preventDefault();
    video.currentTime = Math.max(0, video.currentTime - 10);
  }
};

document.addEventListener("keydown", handleKeyboardShortcuts);

const cleanupHls = () => {
  if (state.videoHlsInstance) {
    state.videoHlsInstance.destroy();
    state.videoHlsInstance = null;
  }
  if (state.watchdog) {
    clearTimeout(state.watchdog);
    state.watchdog = null;
  }
};

const route = () => {
  const hash = location.hash.replace(/^#\/?/, "");
  const [path = "", queryStr = ""] = hash.split("?");
  const [page = "", ...parts] = path.split("/");
  const query = {};
  if (queryStr) {
    queryStr.split("&").forEach(p => {
      const [k, v] = p.split("=");
      query[k] = decodeURIComponent(v || "");
    });
  }
  return { page: page || "home", parts, query };
};

const showToast = (message) => {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
};

const setActive = () => {
  const { page } = route();
  navLinks.forEach((link) => link.classList.toggle("active", link.dataset.nav === page || (page === "home" && link.dataset.nav === "home")));
};

const img = (src, alt, cls = "") => `<img class="${cls}" src="${src}" alt="${alt}" loading="lazy" />`;

const metaPills = (anime) =>
  [anime.type, anime.status, anime.year, anime.rating, anime.language.join("/")]
    .map((item) => `<span class="pill">${item}</span>`)
    .join("");

const card = (anime, compact = false) => {
  const isFavorite = store.getState().favorites.includes(anime.id);
  const isFallback = String(anime.id).startsWith("search-fallback:");
  const isHanime = String(anime.id).startsWith("hanime:");
  const targetHash = isHanime 
    ? `https://hanime.tv/videos/hentai/${anime.id.split("hanime:")[1]}` 
    : isFallback 
      ? `#/search?fallback=${encodeURIComponent(anime.id.split("search-fallback:")[1])}` 
      : `#/anime/${anime.id}`;
  const targetAttr = isHanime ? 'target="_blank" rel="noopener noreferrer"' : '';
  const sub = anime.sub_episodes || anime.latestEpisode || 1;
  const dub = anime.dub_episodes || (anime.language && anime.language.join("/").toLowerCase().includes("dub") ? anime.latestEpisode : 0) || 0;
  
  return `
    <article class="anime-card ${compact ? "compact" : ""}" style="--card-color:${anime.color};--card-accent:${anime.accent}">
      <a href="${targetHash}" ${targetAttr} class="poster-wrap">
        ${img(anime.poster, anime.title, "poster")}
        <span class="score">${anime.score}</span>
      </a>
      <div class="card-body">
        <a href="${targetHash}" ${targetAttr} class="card-title">${anime.title}</a>
        <div class="card-meta">
          <span class="badge-cc">CC ${sub}</span>
          ${dub ? `<span class="badge-dub">🎙️ ${dub}</span>` : ""}
          <span class="type-tag">${anime.type}</span>
        </div>
        <button class="mini-action" data-favorite="${anime.id}" aria-label="Toggle favorite">${isFavorite ? "♥" : "♡"}</button>
      </div>
    </article>
  `;
};

const row = (title, items, action = "") => `
  <section class="content-row">
    <div class="section-head"><h2>${title}</h2>${action}</div>
    <div class="card-scroller">${items.map((item) => card(item)).join("")}</div>
  </section>
`;

const renderHome = async () => {
  const [data, lists] = await Promise.all([
    sourceManager.home(),
    sourceManager.jikanLists().catch((err) => {
      console.warn("Failed to load Jikan lists:", err);
      return null;
    })
  ]);
  const hero = data.spotlight[state.heroIndex % data.spotlight.length];
  const continueItems = store
    .getState()
    .history.map((entry) => animeCatalog.find((anime) => anime.id === entry.animeId))
    .filter(Boolean);
  const isFavorite = store.getState().favorites.includes(hero.id);
  const isHeroHanime = String(hero.id).startsWith("hanime:");
  const heroWatchHref = isHeroHanime 
    ? `https://hanime.tv/videos/hentai/${hero.id.split("hanime:")[1]}` 
    : `#/watch/${hero.id}/1`;
  const heroWatchTarget = isHeroHanime ? 'target="_blank" rel="noopener noreferrer"' : '';

  // Initialize active filter tab if not set
  state.homeFilter = state.homeFilter || "all";
  
  // Filtering logic for "Latest Updates"
  let filteredLatest = data.latest || [];
  if (state.homeFilter === "sub") {
    filteredLatest = filteredLatest.filter(item => 
      (item.language && item.language.join("/").toLowerCase().includes("sub")) || item.sub_episodes
    );
  } else if (state.homeFilter === "dub") {
    filteredLatest = filteredLatest.filter(item => 
      (item.language && item.language.join("/").toLowerCase().includes("dub")) || item.dub_episodes
    );
  } else if (state.homeFilter === "china") {
    filteredLatest = filteredLatest.filter(item => 
      item.type === "ONA" || 
      item.type?.toLowerCase().includes("china") || 
      item.title?.toLowerCase().includes("china") || 
      item.jpTitle?.toLowerCase().includes("china")
    );
  }

  // Get selected calendar day (default to today)
  const today = new Date();
  const dayNameToday = today.toLocaleDateString('en-US', { weekday: 'long' });
  state.selectedCalendarDay = state.selectedCalendarDay || dayNameToday;

  // Filter local schedule items
  const scheduleItems = animeCatalog.filter(anime => 
    anime.schedule && anime.schedule.toLowerCase() === state.selectedCalendarDay.toLowerCase()
  );

  // Generate 5 days centered on today
  const daysToShow = [];
  for (let i = -2; i <= 2; i++) {
    const d = new Date();
    d.setDate(today.getDate() + i);
    daysToShow.push({
      dateObj: d,
      dayName: d.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase(),
      dateStr: String(d.getDate()).padStart(2, '0'),
      dayFull: d.toLocaleDateString('en-US', { weekday: 'long' })
    });
  }

  // Generate lists for 3-column list widget (New Releases, Upcoming, Completed)
  const newReleases = lists?.newReleases?.length
    ? lists.newReleases.slice(0, 20)
    : animeCatalog
        .filter(anime => anime.status === "Ongoing")
        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
        .slice(0, 20);
  const upcomingAnime = lists?.upcoming?.length
    ? lists.upcoming.slice(0, 20)
    : animeCatalog
        .filter(anime => anime.status === "Upcoming")
        .slice(0, 20);
  const completedAnime = lists?.completed?.length
    ? lists.completed.slice(0, 20)
    : animeCatalog
        .filter(anime => anime.status === "Completed")
        .slice(0, 20);

  view.innerHTML = `
    <!-- Hero Spotlight Section -->
    <section class="hero" style="background-image:linear-gradient(rgba(11,14,17,0.58), rgba(11,14,17,0.92)), url('${hero.banner}')">
      <div class="hero-upper-row">
        <span class="spotlight-tag">#${(state.heroIndex % data.spotlight.length) + 1} Spotlight</span>
      </div>
      
      <div class="hero-lower-row">
        <div class="hero-details">
          <h1 class="hero-title">${hero.title}</h1>
          <p class="hero-desc">${hero.description}</p>
          
          <div class="hero-meta-box">
            <div class="meta-item">
              <span class="meta-label">Rating</span>
              <span class="meta-val">${hero.rating || 'PG-13'}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Release</span>
              <span class="meta-val">${hero.year || 'TBA'}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Quality</span>
              <span class="meta-val">HD</span>
            </div>
          </div>
          
          <div class="hero-actions-row">
            <a class="button primary watch-now-btn" href="${heroWatchHref}" ${heroWatchTarget}>▶ WATCH NOW</a>
            <button class="bookmark-btn" data-favorite="${hero.id}">${isFavorite ? "♥" : "♡"}</button>
          </div>
        </div>
        
        <div class="hero-carousel-controls">
          <button class="carousel-btn" data-hero-nav="prev">⟨</button>
          <span class="carousel-indicator">${(state.heroIndex % data.spotlight.length) + 1} / ${data.spotlight.length}</span>
          <button class="carousel-btn" data-hero-nav="next">⟩</button>
        </div>
      </div>
    </section>

    <!-- Alert Announcement Banner -->
    <div class="announcement-banner">
      <span class="announcement-banner-icon">📢</span>
      <div class="announcement-banner-text">
        Welcome to <strong>Nompyr</strong>! Search, recommend, and discover over 40k+ anime.
      </div>
    </div>

    <!-- Share Bar -->
    <div class="share-bar">
      <div class="share-left">
        <div class="share-avatar-wrapper">💬</div>
        <div class="share-text">
          <span class="share-title">12.8k Shares</span>
          <span class="share-desc">Share Nompyr with your friends!</span>
        </div>
      </div>
      <div class="share-right">
        <a href="https://t.me/share/url?url=http://127.0.0.1:4173/&text=Nompyr%20-%20Watch%20anime%20online!" target="_blank" class="share-btn telegram">✈ Telegram</a>
        <a href="https://twitter.com/intent/tweet?url=http://127.0.0.1:4173/" target="_blank" class="share-btn twitter">𝕏 Twitter</a>
        <a href="https://facebook.com/sharer/sharer.php?u=http://127.0.0.1:4173/" target="_blank" class="share-btn facebook">Facebook</a>
        <a href="https://reddit.com/submit?url=http://127.0.0.1:4173/" target="_blank" class="share-btn reddit">Reddit</a>
        <button class="share-btn generic-copy" id="shareCopyLinkBtn">🔗 Copy Link</button>
      </div>
    </div>

    <!-- Double Columns Layout -->
    <div class="home-columns-layout">
      <!-- Left Column (Main Content) -->
      <div class="home-main-col">
        <!-- Continue Watching (if history exists) -->
        ${continueItems.length ? `
          <section class="content-row">
            <div class="section-head"><h2>Continue Watching</h2></div>
            <div class="card-scroller">
              ${continueItems.map(item => card(item)).join("")}
            </div>
          </section>
        ` : ""}

        <!-- Latest Updates Section with Filter Tabs -->
        <section class="content-row">
          <div class="section-head flex-section-head">
            <h2>Latest Updates</h2>
            <div class="filter-tabs">
              <button class="filter-tab ${state.homeFilter === 'all' ? 'active' : ''}" data-home-filter="all">All</button>
              <button class="filter-tab ${state.homeFilter === 'sub' ? 'active' : ''}" data-home-filter="sub">Sub</button>
              <button class="filter-tab ${state.homeFilter === 'dub' ? 'active' : ''}" data-home-filter="dub">Dub</button>
              <button class="filter-tab ${state.homeFilter === 'china' ? 'active' : ''}" data-home-filter="china">China</button>
            </div>
          </div>
          <div class="grid home-latest-grid">
            ${filteredLatest.slice(0, 18).map(item => card(item)).join("")}
          </div>
        </section>

        <!-- Three-Column list widget [New Releases, Upcoming, Completed] -->
        <div class="three-col-list-widget">
          <!-- Column 1: New Releases -->
          <div class="list-widget-col">
            <h3 class="list-widget-col-title">🚀 New Releases</h3>
            <div class="list-widget-items">
              ${newReleases.map(anime => `
                <div class="list-widget-item">
                  <a href="#/anime/${anime.id}">
                    <img src="${anime.poster}" class="list-widget-thumb" />
                  </a>
                  <div class="list-widget-details">
                    <a href="#/anime/${anime.id}" class="list-widget-title">${anime.title}</a>
                    <div class="list-widget-meta">
                      <span class="badge-cc">CC ${anime.latestEpisode}</span>
                      ${anime.language.includes("Dub") ? `<span class="badge-dub">🎙️ Dub</span>` : ""}
                      <span class="type-tag">${anime.type}</span>
                    </div>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Column 2: Upcoming -->
          <div class="list-widget-col">
            <h3 class="list-widget-col-title">📅 Upcoming Anime</h3>
            <div class="list-widget-items">
              ${upcomingAnime.map(anime => `
                <div class="list-widget-item">
                  <a href="#/anime/${anime.id}">
                    <img src="${anime.poster}" class="list-widget-thumb" />
                  </a>
                  <div class="list-widget-details">
                    <a href="#/anime/${anime.id}" class="list-widget-title">${anime.title}</a>
                    <div class="list-widget-meta">
                      <span class="type-tag">${anime.type}</span>
                      <span class="pill" style="font-size:0.65rem;">${anime.season} ${anime.year}</span>
                    </div>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Column 3: Completed -->
          <div class="list-widget-col">
            <h3 class="list-widget-col-title">✅ Completed</h3>
            <div class="list-widget-items">
              ${completedAnime.map(anime => `
                <div class="list-widget-item">
                  <a href="#/anime/${anime.id}">
                    <img src="${anime.poster}" class="list-widget-thumb" />
                  </a>
                  <div class="list-widget-details">
                    <a href="#/anime/${anime.id}" class="list-widget-title">${anime.title}</a>
                    <div class="list-widget-meta">
                      <span class="badge-cc">CC ${anime.episodes}</span>
                      ${anime.language.includes("Dub") ? `<span class="badge-dub">🎙️ Dub</span>` : ""}
                      <span class="type-tag">${anime.type}</span>
                    </div>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>

        <!-- A-Z Alphabet List -->
        <div class="az-panel">
          <div class="section-head">
            <h2>🔤 A-Z List</h2>
          </div>
          <div class="az-row">
            ${['All', '0-9', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')].map(char => `
              <button class="az-chip" data-az-chip="${char}">${char}</button>
            `).join("")}
          </div>
        </div>

        <!-- Branded Footer -->
        <footer class="branded-footer">
          <div class="footer-top">
            <a class="brand" href="#/">
              <span class="brand-nom">Nom</span><span class="brand-pyr">pyr</span>
            </a>
            <div class="footer-links">
              <a href="#/search">Anime List</a>
              <a href="#/schedule">Schedule</a>
              <a href="#/recommender">Recommender</a>
              <a href="#/profile">Profile Settings</a>
            </div>
          </div>
          <div class="footer-bottom">
            <p>Nompyr is a demo prototype client. Playback features represent simulation. External provider connectivity requires a configured Data API key in the admin control board.</p>
            <p style="margin-top:0.5rem;">© 2026 Nompyr. All rights reserved.</p>
          </div>
        </footer>
      </div>

      <!-- Right Sidebar Column -->
      <aside class="home-side-col">
        <!-- Top Trending (1-10 Ranked List) -->
        <div class="panel side-trending-panel">
          <div class="side-panel-header">
            <h2>🔥 Top Trending</h2>
            <a href="#/trending">View all</a>
          </div>
          <div class="trending-list">
            ${data.trending.slice(0, 10).map((item, index) => {
              const isFallback = String(item.id).startsWith("search-fallback:");
              const isHanime = String(item.id).startsWith("hanime:");
              const targetHash = isHanime 
                ? `https://hanime.tv/videos/hentai/${item.id.split("hanime:")[1]}` 
                : isFallback 
                  ? `#/search?fallback=${encodeURIComponent(item.id.split("search-fallback:")[1])}` 
                  : `#/anime/${item.id}`;
              const targetAttr = isHanime ? 'target="_blank" rel="noopener noreferrer"' : '';
              const sub = item.sub_episodes || item.latestEpisode || 1;
              const dub = item.dub_episodes || (item.language && item.language.join("/").toLowerCase().includes("dub") ? item.latestEpisode : 0) || 0;
              return `
                <a href="${targetHash}" ${targetAttr} class="trending-item">
                  <span class="trending-rank rank-${index + 1}">#${index + 1}</span>
                  <img class="trending-item-poster" src="${item.poster}" alt="${item.title}" />
                  <div class="trending-item-details">
                    <span class="trending-item-title">${item.title}</span>
                    <div class="trending-item-meta" style="display:flex;align-items:center;gap:0.35rem;margin-top:0.2rem;">
                      <span class="badge-cc">CC ${sub}</span>
                      ${dub ? `<span class="badge-dub">🎙️ ${dub}</span>` : ""}
                      <span class="type-tag">${item.type}</span>
                    </div>
                  </div>
                </a>
              `;
            }).join("")}
          </div>
        </div>

        <!-- Weekly Calendar Dashboard Widget -->
        <div class="panel side-calendar-panel" style="margin-top:1.5rem;">
          <div class="calendar-header">
            <div class="calendar-title-wrap">
              <h2>📅 Schedule Calendar</h2>
              <div class="calendar-clock" id="calendarClock">00:00:00 AM</div>
            </div>
            <span class="expand-chevron" id="calendarExpandBtn" title="Go to weekly schedule">▼</span>
          </div>
          
          <div class="calendar-days-row">
            ${daysToShow.map(d => {
              const isActive = d.dayFull.toLowerCase() === state.selectedCalendarDay.toLowerCase();
              return `
                <button class="calendar-day-btn ${isActive ? 'active' : ''}" data-calendar-day="${d.dayFull}">
                  <span class="cal-day-name">${d.dayName}</span>
                  <span class="cal-date-num">${d.dateStr}</span>
                </button>
              `;
            }).join("")}
          </div>

          <div class="calendar-schedule-list">
            ${scheduleItems.length ? scheduleItems.map(item => {
              const isHanime = String(item.id).startsWith("hanime:");
              const targetHash = isHanime 
                ? `https://hanime.tv/videos/hentai/${item.id.split("hanime:")[1]}` 
                : `#/anime/${item.id}`;
              const targetAttr = isHanime ? 'target="_blank" rel="noopener noreferrer"' : '';
              return `
                <a href="${targetHash}" ${targetAttr} class="cal-schedule-item">
                  <span class="cal-item-time">${item.duration || '24m'}</span>
                  <div class="cal-item-info">
                    <span class="cal-item-title">${item.title}</span>
                    <span class="cal-item-ep">Episode ${item.latestEpisode || 1}</span>
                  </div>
                </a>
              `;
            }).join("") : `<div class="empty-schedule">No releases scheduled for ${state.selectedCalendarDay}.</div>`}
          </div>
        </div>
      </aside>
    </div>
  `;

  // Start ticking clock immediately
  const updateClock = () => {
    const clockEl = document.getElementById("calendarClock");
    if (clockEl) {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: true });
    }
  };
  updateClock();
  if (state.clockInterval) clearInterval(state.clockInterval);
  state.clockInterval = setInterval(updateClock, 1000);
};

const filtersMarkup = () => {
  const genresList = [
    "Action", "Adventure", "Comedy", "Drama", "Fantasy", "Gourmet", "Mystery", 
    "Sci-Fi", "School", "Seinen", "Shounen", "Slice of Life", "Supernatural", "Suspense",
    "Romance", "Sports", "Thriller", "Mecha", "Historical", "Psychological", "Isekai",
    "Hentai", "Censored", "Uncensored", "Yuri", "Anal", "Milf", "Tentacle", "OVA"
  ].sort();

  const years = Array.from({ length: 37 }, (_, i) => 2026 - i);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const days = Array.from({ length: 31 }, (_, i) => i + 1);

  if (!state.filters.genres) state.filters.genres = [];

  const typeOptions = ["TV", "Movie", "OVA", "ONA", "Special", "Music"];
  const statusOptions = ["Ongoing", "Completed", "Upcoming"];
  const ratingOptions = ["G", "PG", "PG-13", "R", "R+", "Rx"];
  const scoreOptions = Array.from({ length: 10 }, (_, i) => 10 - i);
  const seasonOptions = ["Spring", "Summer", "Fall", "Winter"];
  const languageOptions = ["Sub", "Dub", "Sub & Dub"];
  
  const sortOptions = [
    { value: "score_desc", label: "Score (High to Low)" },
    { value: "latest_desc", label: "Latest Updates" },
    { value: "year_desc", label: "Year (New to Old)" },
    { value: "year_asc", label: "Year (Old to New)" },
    { value: "title_asc", label: "Title (A-Z)" },
    { value: "title_desc", label: "Title (Z-A)" }
  ];

  return `
    <aside class="filters">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem;">
        <h2 style="margin:0;">Filters</h2>
        <button type="button" class="search-filter-btn" id="resetFiltersBtn" style="background:rgba(231,111,81,0.15);color:var(--danger);">Reset All</button>
      </div>

      <div class="filters-grid-container">
        <!-- Search Input -->
        <div class="filters-group" style="grid-column: 1 / -1;">
          <label>Search Library</label>
          <div class="search-input-wrap" style="position:relative;width:100%;">
            <input id="localSearch" type="search" placeholder="Search library..." value="${state.filters.query || ""}" autocomplete="off" />
            <div id="localSearchSuggestions" class="search-suggestions-dropdown hidden"></div>
          </div>
        </div>

        <!-- Type -->
        <div class="filters-group">
          <label for="typeFilter">Type</label>
          <select id="typeFilter">
            <option value="">All Types</option>
            ${typeOptions.map(t => `<option ${state.filters.type === t ? "selected" : ""} value="${t}">${t}</option>`).join("")}
          </select>
        </div>

        <!-- Status -->
        <div class="filters-group">
          <label for="statusFilter">Status</label>
          <select id="statusFilter">
            <option value="">All Status</option>
            ${statusOptions.map(s => `<option ${state.filters.status === s ? "selected" : ""} value="${s}">${s}</option>`).join("")}
          </select>
        </div>

        <!-- Rating -->
        <div class="filters-group">
          <label for="ratingFilter">Rated</label>
          <select id="ratingFilter">
            <option value="">All Ratings</option>
            ${ratingOptions.map(r => `<option ${state.filters.rating === r ? "selected" : ""} value="${r}">${r}</option>`).join("")}
          </select>
        </div>

        <!-- Score -->
        <div class="filters-group">
          <label for="scoreFilter">Min Score</label>
          <select id="scoreFilter">
            <option value="">Any Score</option>
            ${scoreOptions.map(s => `<option ${String(state.filters.score) === String(s) ? "selected" : ""} value="${s}">${s}+ ★</option>`).join("")}
          </select>
        </div>

        <!-- Season -->
        <div class="filters-group">
          <label for="seasonFilter">Season</label>
          <select id="seasonFilter">
            <option value="">All Seasons</option>
            ${seasonOptions.map(s => `<option ${state.filters.season === s.toLowerCase() ? "selected" : ""} value="${s.toLowerCase()}">${s}</option>`).join("")}
          </select>
        </div>

        <!-- Language -->
        <div class="filters-group">
          <label for="languageFilter">Language</label>
          <select id="languageFilter">
            <option value="">All Langs</option>
            ${languageOptions.map(l => `<option ${state.filters.language === l ? "selected" : ""} value="${l}">${l}</option>`).join("")}
          </select>
        </div>

        <!-- Sort -->
        <div class="filters-group" style="grid-column: span 2;">
          <label for="sortFilter">Sort By</label>
          <select id="sortFilter">
            ${sortOptions.map(o => `<option ${state.filters.sort === o.value ? "selected" : ""} value="${o.value}">${o.label}</option>`).join("")}
          </select>
        </div>

        <!-- Start Date -->
        <div class="filters-group" style="grid-column: span 2;">
          <label>Start Date</label>
          <div class="date-inputs-row">
            <select id="startYearFilter">
              <option value="">Year</option>
              ${years.map(y => `<option ${String(state.filters.startYear) === String(y) ? "selected" : ""} value="${y}">${y}</option>`).join("")}
            </select>
            <select id="startMonthFilter">
              <option value="">Month</option>
              ${months.map(m => `<option ${String(state.filters.startMonth) === String(m) ? "selected" : ""} value="${m}">${m}</option>`).join("")}
            </select>
            <select id="startDayFilter">
              <option value="">Day</option>
              ${days.map(d => `<option ${String(state.filters.startDay) === String(d) ? "selected" : ""} value="${d}">${d}</option>`).join("")}
            </select>
          </div>
        </div>

        <!-- End Date -->
        <div class="filters-group" style="grid-column: span 2;">
          <label>End Date</label>
          <div class="date-inputs-row">
            <select id="endYearFilter">
              <option value="">Year</option>
              ${years.map(y => `<option ${String(state.filters.endYear) === String(y) ? "selected" : ""} value="${y}">${y}</option>`).join("")}
            </select>
            <select id="endMonthFilter">
              <option value="">Month</option>
              ${months.map(m => `<option ${String(state.filters.endMonth) === String(m) ? "selected" : ""} value="${m}">${m}</option>`).join("")}
            </select>
            <select id="endDayFilter">
              <option value="">Day</option>
              ${days.map(d => `<option ${String(state.filters.endDay) === String(d) ? "selected" : ""} value="${d}">${d}</option>`).join("")}
            </select>
          </div>
        </div>
      </div>

      <!-- Genres Chips Container -->
      <div style="margin-top: 1.25rem;">
        <label style="font-size:0.72rem;font-weight:750;text-transform:uppercase;color:var(--muted);letter-spacing:0.05em;">Genres</label>
        <div class="genre-chips-container">
          ${genresList.map(g => {
            const isActive = state.filters.genres.includes(g);
            return `<span class="filter-chip ${isActive ? "active" : ""}" data-genre-chip="${g}">${g}</span>`;
          }).join("")}
        </div>
      </div>
    </aside>
  `;
};

const renderSearch = async (title = "Search") => {
  const { query: queryParams } = route();
  if (queryParams.fallback) {
    state.filters.query = queryParams.fallback;
    const sInput = document.querySelector("#searchInput");
    if (sInput) sInput.value = queryParams.fallback;
    history.replaceState(null, "", "#/search");
  }
  if (!state.filters.page) state.filters.page = 1;
  const searchData = await sourceManager.search(state.filters);
  let results = searchData.results;
  if (state.filters.az) {
    if (state.filters.az === "0-9") {
      results = results.filter(item => /^[0-9]/.test(item.title));
    } else {
      results = results.filter(item => item.title.toUpperCase().startsWith(state.filters.az.toUpperCase()));
    }
  }
  const total = state.filters.az ? results.length : searchData.total;
  const currentPage = searchData.page;
  const totalPages = Math.ceil(total / 30) || 1;
  const isEmpty = results.length === 0;
  const isApi = sourceManager.apiStatus().contentReady;
  
  const emptyMarkup = isEmpty
    ? `<div class="empty-state">
        <div class="empty-icon">⌕</div>
        <h3>No anime found</h3>
        <p>${isApi ? "Try adjusting the filters or refining your search term." : "No matches in the library."}</p>
        ${isApi ? `
          <div class="suggestions-box">
            <span>Try searching:</span>
            <div class="suggestion-chips">
              <button class="chip-btn" data-search="One Piece">One Piece</button>
              <button class="chip-btn" data-search="Slime">Slime</button>
              <button class="chip-btn" data-search="Re:ZERO">Re:ZERO</button>
              <button class="chip-btn" data-search="School">School</button>
            </div>
          </div>
        ` : ""}
       </div>`
    : "";

  const paginationMarkup = totalPages > 1
    ? `<div class="search-pagination" style="display:flex;justify-content:center;align-items:center;gap:1.5rem;margin-top:2.5rem;padding-top:1.5rem;border-top:1px solid var(--border);">
        <button class="button ghost pag-btn" data-pag="prev" ${currentPage <= 1 ? 'disabled' : ''} style="min-height:2.4rem;padding:0 1.25rem;">⟨ Prev</button>
        <span class="pag-indicator" style="font-weight:750;font-size:0.92rem;color:var(--muted);">Page ${currentPage} of ${totalPages}</span>
        <button class="button ghost pag-btn" data-pag="next" ${currentPage >= totalPages ? 'disabled' : ''} style="min-height:2.4rem;padding:0 1.25rem;">Next ⟩</button>
       </div>`
    : "";

  view.innerHTML = `
    <div class="browse-layout">
      ${filtersMarkup()}
      <section>
        <div class="page-head"><span>${total} anime found</span><h1>${title}</h1></div>
        ${isEmpty ? emptyMarkup : `
          <div class="grid">${results.map((item) => card(item)).join("")}</div>
          ${paginationMarkup}
        `}
      </section>
    </div>
  `;
};

const renderCollection = async (kind) => {
  const data = await sourceManager.home();
  const map = { trending: data.trending, latest: data.latest, popular: data.popular };
  view.innerHTML = `
    <div class="page-head"><span>${map[kind]?.length || 0} anime</span><h1>${kind[0].toUpperCase() + kind.slice(1)}</h1></div>
    <div class="grid">${(map[kind] || data.trending).map((item) => card(item)).join("")}</div>
  `;
};

const renderAnime = async (slug) => {
  const [anime, episodes] = await Promise.all([sourceManager.anime(slug), sourceManager.episodes(slug)]);
  const isFavorite = store.getState().favorites.includes(anime.id);
  const related = animeCatalog.filter((item) => item.id !== anime.id && item.genres.some((genre) => anime.genres.includes(genre))).slice(0, 4);
  view.innerHTML = `
    <section class="detail-hero" style="--hero-color:${anime.color};background-image:linear-gradient(90deg, rgba(6,9,15,.96), rgba(6,9,15,.62)), url('${anime.banner}')">
      ${img(anime.poster, anime.title, "detail-poster")}
      <div class="detail-copy">
        <span class="eyebrow">${anime.jpTitle}</span>
        <h1>${anime.title}</h1>
        <p>${anime.description}</p>
        <div class="hero-pills">${metaPills(anime)}<span class="pill">${anime.studio}</span></div>
        <div class="hero-actions">
          <a class="button primary" href="#/watch/${anime.id}/${Math.max(1, anime.latestEpisode)}">▶ Watch Latest</a>
          <button class="button ghost" data-favorite="${anime.id}">${isFavorite ? "♥ Favorited" : "♡ Favorite"}</button>
        </div>
      </div>
    </section>
    <div class="two-column">
      <section class="panel" style="display:flex; flex-direction:column; gap:1.5rem;">
        <div style="display:flex; flex-direction:column; gap:0.5rem;">
          <div class="section-head" style="margin-bottom:0.25rem;">
            <h2>Select Episode</h2>
            <span style="font-size:0.85rem; color:var(--muted);">${anime.latestEpisode}/${anime.episodes} episodes available</span>
          </div>
          <div class="compact-episodes" style="display:flex; flex-wrap:wrap; gap:0.5rem; max-height:160px; overflow-y:auto; padding-right:0.25rem;">
            ${episodes.map((episode) => `
              <a class="ep-btn ${episode.released ? "" : "disabled"}" href="${episode.released ? `#/watch/${anime.id}/${episode.number}` : "#"}" 
                 style="display:inline-grid; place-items:center; width:2.5rem; height:2.5rem; border-radius:50%; background:rgba(255,255,255,0.08); color:var(--text); font-size:0.9rem; font-weight:500; text-decoration:none; transition:all 0.2s;"
                 onmouseover="this.style.background='var(--accent)'; this.style.color='#fff'; this.style.transform='scale(1.15)';"
                 onmouseout="this.style.background='rgba(255,255,255,0.08)'; this.style.color='var(--text)'; this.style.transform='scale(1.0)';">
                ${episode.number}
              </a>
            `).join("")}
          </div>
        </div>
        
        <div style="display:flex; flex-direction:column; gap:0.5rem;">
          <div class="section-head"><h2>Official Trailer</h2></div>
          ${anime.trailer_url ? `
            <div class="trailer-container" style="position:relative; width:100%; padding-bottom:56.25%; height:0; border-radius:0.65rem; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,0.5);">
              <iframe src="${anime.trailer_url}" style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
          ` : `
            <div style="padding:2.5rem 1rem; text-align:center; background:rgba(255,255,255,0.03); border-radius:0.65rem; color:var(--muted); font-size:0.9rem; border:1px dashed rgba(255,255,255,0.1);">
              <span>No official trailer available for this anime.</span>
            </div>
          `}
        </div>
      </section>
      <aside class="panel">
        <h2>Metadata</h2>
        <dl class="meta-list">
          <dt>Type</dt><dd>${anime.type}</dd>
          <dt>Status</dt><dd>${anime.status}</dd>
          <dt>Score</dt><dd>⭐ ${anime.score}</dd>
          <dt>Genres</dt><dd>${anime.genres.join(", ")}</dd>
          <dt>Studio</dt><dd>${anime.studio}</dd>
          <dt>Year</dt><dd>${anime.year}</dd>
          <dt>Rating</dt><dd>${anime.rating}</dd>
          <dt>Schedule</dt><dd>${anime.schedule}</dd>
          <dt>Source Health</dt><dd>${anime.sourceHealth}</dd>
        </dl>
      </aside>
    </div>
    ${row("Recommendations", related)}
  `;
};

const getMockComments = (animeTitle) => {
  const templates = [
    { user: "AnimeFan99", text: `This episode of ${animeTitle} was absolutely amazing! The animation quality is top-tier.`, date: "2 hours ago" },
    { user: "OtakuSakura", text: `I've been waiting for this episode all week! Can't wait to see what happens next.`, date: "5 hours ago" },
    { user: "LuffyGamer", text: `The soundtrack during the climax scene gave me goosebumps. 10/10!`, date: "1 day ago" },
    { user: "Sora_No_Kiseki", text: `Is it just me or is the pacing getting much better? Really enjoying this adaptation.`, date: "1 day ago" },
    { user: "MysteryWatcher", text: `Such a cliffhanger at the end! Anyone know when the next episode drops?`, date: "2 days ago" }
  ];
  return templates.sort(() => 0.5 - Math.random()).slice(0, 3);
};

const getCommentsForAnime = (animeId, animeTitle) => {
  const key = `nompyr-comments-${animeId}`;
  const saved = localStorage.getItem(key);
  if (saved) return JSON.parse(saved);
  const mock = getMockComments(animeTitle);
  localStorage.setItem(key, JSON.stringify(mock));
  return mock;
};

const saveComment = (animeId, comment) => {
  const key = `nompyr-comments-${animeId}`;
  const list = getCommentsForAnime(animeId, "");
  list.unshift(comment);
  localStorage.setItem(key, JSON.stringify(list));
};

const loadWatchRecommendations = async (anime, container) => {
  let related = [];
  try {
    const jikanRecs = await sourceManager.recommendations(anime.title);
    if (jikanRecs && jikanRecs.length > 0) {
      // Exclude current anime from Jikan recommendations
      const filteredJikan = jikanRecs.filter(item => item.id !== anime.id);
      related.push(...filteredJikan);
    }
  } catch (err) {
    console.warn("Jikan recommendations failed:", err);
  }

  if (related.length < 4 && anime.genres && anime.genres.length > 0) {
    try {
      const activeGenre = anime.genres[0];
      const searchRes = await sourceManager.search({
        query: "",
        genre: activeGenre.toLowerCase(),
        type: (anime.type || "TV").toLowerCase()
      });
      const searchItems = searchRes?.results || [];
      const filteredSearch = searchItems.filter(item => 
        item.id !== anime.id && 
        item.type === anime.type && 
        item.genres.some(g => anime.genres.includes(g)) && 
        !related.some(r => r.id === item.id)
      );
      related.push(...filteredSearch);
    } catch (err) {
      console.warn("Genre/type search fallback failed:", err);
    }
  }

  if (related.length === 0) {
    // Fallback static catalog match: Prioritize same type AND overlapping genres
    related = animeCatalog.filter((item) => 
      item.id !== anime.id && 
      item.type === anime.type && 
      item.genres.some((genre) => anime.genres.includes(genre))
    );
    
    // Relax type constraint if less than 6 matches
    if (related.length < 6) {
      const more = animeCatalog.filter((item) => 
        item.id !== anime.id && 
        item.type !== anime.type && 
        item.genres.some((genre) => anime.genres.includes(genre)) &&
        !related.some(r => r.id === item.id)
      );
      related.push(...more);
    }
  }

  related = related.slice(0, 6);

  if (related.length > 0) {
    container.innerHTML = `
      <section class="content-row">
        <div class="section-head"><h2 style="color: var(--accent);">Recommended For You</h2></div>
        <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr)); gap: 1rem;">
          ${related.map((item) => card(item)).join("")}
        </div>
      </section>
    `;
  } else {
    container.innerHTML = `<p class="muted" style="padding: 1rem 0; font-size: 0.85rem; color: var(--muted);">No similar recommendations found.</p>`;
  }
};

const renderWatch = async (slug, episodeNo = "1") => {
  const currentEpKey = `${slug}-${episodeNo}`;
  if (state.currentEpisodeId !== currentEpKey) {
    state.currentEpisodeId = currentEpKey;
    state.activeServerId = null;
    state.activeLanguage = null;
  }

  const anime = await sourceManager.anime(slug);
  const episodes = await sourceManager.episodes(slug);
  const episode = episodes.find((item) => String(item.number) === String(episodeNo)) || episodes.at(-1);
  const servers = await sourceManager.servers(episode.id);

  const modes = [...new Set(servers.map(s => s.mode.toLowerCase()))];
  if (!state.activeLanguage || !modes.includes(state.activeLanguage)) {
    state.activeLanguage = modes.includes("sub") ? "sub" : modes[0] || "sub";
  }

  const filteredServers = servers.filter(s => s.mode.toLowerCase() === state.activeLanguage);
  if (!state.activeServerId || !filteredServers.some(s => s.id === state.activeServerId)) {
    state.activeServerId = filteredServers[0]?.id || null;
  }

  let stream = { hls: "", message: "No server available.", intro: [0, 0], outro: [0, 0] };
  if (state.activeServerId) {
    stream = await sourceManager.stream(state.activeServerId);
  }

  const progress = store.getState().progress[episode.id] || 0;
  const isDirectMp4 = stream.type === "mp4" || stream.hls.split('?')[0].toLowerCase().endsWith(".mp4") || stream.hls.toLowerCase().includes(".mp4");

  // Fetch popular items for the sidebar list
  let popularItems = [];
  try {
    const homeData = await sourceManager.home();
    popularItems = homeData?.popular || [];
  } catch (err) {
    console.warn("Failed to fetch popular items:", err);
  }
  if (!popularItems || popularItems.length === 0) {
    popularItems = animeCatalog;
  }
  popularItems = popularItems.slice(0, 6);

  const subServers = servers.filter(s => s.mode.toLowerCase() === "sub");
  const dubServers = servers.filter(s => s.mode.toLowerCase() === "dub");

  view.innerHTML = `
    <div class="hianime-watch-container">
      <div class="hianime-main-row">
        <!-- 1. Left Sidebar: Episode List -->
        <div class="hianime-episodes-sidebar">
          <div style="padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;">
            <span style="font-size: 0.85rem; font-weight: bold; color: #fff;">List of episodes:</span>
            <div style="position: relative; flex-grow: 1; max-width: 120px;">
              <input type="text" id="epSearchInput" placeholder="Number of Ep" style="width: 100%; padding: 0.35rem 0.5rem; font-size: 0.75rem; background: rgba(0,0,0,0.25); border: 1px solid var(--border); border-radius: 0.25rem; color: #fff; outline:none;" />
            </div>
          </div>
          <div class="hianime-ep-list" id="epListContainer">
            ${episodes.map((item) => `
              <a class="ep-link-item ${String(item.number) === String(episodeNo) ? "active" : ""} ${item.released ? "" : "disabled"}" data-ep-num="${item.number}" href="${item.released ? `#/watch/${anime.id}/${item.number}` : "#"}">
                <span style="width: 20px; text-align: center; color: var(--muted); font-size: 0.8rem; font-weight: bold;">${item.number}</span>
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1;" title="${item.title}">${item.title}</span>
                ${String(item.number) === String(episodeNo) ? `<span style="font-size: 0.8rem; color: #e76f51;">▶</span>` : ""}
              </a>
            `).join("")}
          </div>
        </div>

        <!-- 2. Center: Player & Servers -->
        <div class="hianime-player-section">
          <div class="player ${store.getState().settings.theatre ? "theatre" : ""}" style="width:100%; border-radius: 0.65rem; overflow:hidden;">
            ${stream.hls ? `
              <div class="player-container" style="width:100%; height:100%;">
                <video id="videoPlayer" class="video-player" controls playsinline ${isDirectMp4 ? "" : 'crossorigin="anonymous"'} style="width:100%; height:100%;">
                  ${(stream.tracks || []).map(t => `<track src="${t.file}" label="${t.label}" kind="${t.kind || 'captions'}" srclang="${t.label.toLowerCase()}" ${t.default ? 'default' : ''}>`).join('')}
                </video>
                <div id="playerOverlay" class="player-overlay"></div>
              </div>
            ` : (stream.embed_url || stream.embedUrl) ? `
              <div class="player-container" style="width:100%; height:100%;">
                <iframe src="${stream.embed_url || stream.embedUrl}" class="video-player" allow="autoplay; fullscreen" sandbox="allow-scripts allow-same-origin allow-forms" style="width:100%;height:100%;border:none;"></iframe>
              </div>
            ` : `
              <div class="player-art" style="background-image:linear-gradient(rgba(7,10,16,.25),rgba(7,10,16,.85)),url('${anime.banner}')"></div>
              <div class="player-message">
                <span>Demo Player</span>
                <h1>${anime.title}</h1>
                <p>${stream.message || "Streaming is disabled/not resolved for this server."}</p>
                <button class="button primary" id="simulateProgress">Simulate Watch Progress</button>
              </div>
              <div class="progress"><span style="width:${progress}%"></span></div>
            `}
          </div>

          <!-- Player Control Options Bar -->
          <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(17, 22, 26, 0.85); padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
              <span style="cursor:pointer;" id="actionExpand">🔍 Expand</span>
              <span style="cursor:pointer;" id="actionLight">💡 Light <strong>On</strong></span>
              <span style="cursor:pointer;" id="actionAutoplay">🔄 Auto Play <strong>Off</strong></span>
              <span style="cursor:pointer;" id="actionAutonext">⏭️ Auto Next <strong>Off</strong></span>
              <span style="cursor:pointer;" id="actionAutoSkip">⏩ Auto Skip Intro <strong>Off</strong></span>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center;">
              <a href="#/watch/${anime.id}/${Math.max(1, Number(episodeNo) - 1)}" style="cursor:pointer;" title="Previous Episode">⏮️</a>
              <a href="#/watch/${anime.id}/${Math.min(anime.episodes, Number(episodeNo) + 1)}" style="cursor:pointer;" title="Next Episode">⏭️</a>
              ${state.activeServerId ? `<span style="cursor:pointer;" data-download="${state.activeServerId}" title="Download">➕</span>` : ""}
              ${stream.hls ? `
                <span style="cursor:pointer;" data-pip="true" title="Picture in Picture">📶</span>
                <span style="cursor:pointer;" data-fullscreen="true" title="Fullscreen">⛶</span>
              ` : ""}
            </div>
          </div>

          <!-- Yellow Card & Server Groups -->
          <div class="hianime-servers-box">
            <div class="hianime-server-alert">
              <span style="font-size: 0.8rem; color: #856404; font-weight: normal; margin-bottom: 0.15rem;">You are watching</span>
              <strong style="font-size: 1.1rem; color: #856404; margin-bottom: 0.25rem;">Episode ${episodeNo}</strong>
              <span style="font-size: 0.72rem; color: #9c7a1e; line-height: 1.3;">If current server doesn't work please try other servers beside.</span>
            </div>
            <div class="hianime-server-list-wrap">
              <div style="display: flex; align-items: flex-start; gap: 1rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 0.75rem;">
                <span style="width: 50px; font-size: 0.8rem; font-weight: bold; color: var(--muted); padding-top: 0.35rem;">SUB:</span>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  ${subServers.map((server) => `
                    <button class="server ${state.activeServerId === server.id ? "active" : ""}" data-server-id="${server.id}" data-mode="sub" style="height: auto; padding: 0.4rem 0.8rem; font-size: 0.8rem; display: inline-flex; align-items: center; justify-content: center;">
                      ${server.label}
                    </button>
                  `).join("") || `<span style="font-size:0.8rem; color:var(--muted); padding-top:0.35rem;">No SUB servers</span>`}
                </div>
              </div>
              <div style="display: flex; align-items: flex-start; gap: 1rem;">
                <span style="width: 50px; font-size: 0.8rem; font-weight: bold; color: var(--muted); padding-top: 0.35rem;">DUB:</span>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  ${dubServers.map((server) => `
                    <button class="server ${state.activeServerId === server.id ? "active" : ""}" data-server-id="${server.id}" data-mode="dub" style="height: auto; padding: 0.4rem 0.8rem; font-size: 0.8rem; display: inline-flex; align-items: center; justify-content: center;">
                      ${server.label}
                    </button>
                  `).join("") || `<span style="font-size:0.8rem; color:var(--muted); padding-top:0.35rem;">No DUB servers</span>`}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Right Sidebar: Info Panel -->
        <div class="hianime-info-sidebar">
          <div style="display: flex; gap: 1rem; align-items: flex-start;">
            <img src="${anime.poster}" style="width: 80px; height: 115px; object-fit: cover; border-radius: 0.35rem; border: 1px solid var(--border);" />
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
              <h1 style="font-size: 0.95rem; margin: 0; color: #fff; line-height: 1.3; font-weight: bold; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${anime.title}">${anime.title}</h1>
              <div style="display: flex; gap: 0.3rem; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.08); color: #fff; font-size: 0.65rem; padding: 0.15rem 0.35rem; border-radius: 0.2rem; font-weight: bold; border: 1px solid var(--border);">G</span>
                <span style="background: #e76f51; color:#fff; font-size: 0.65rem; padding: 0.15rem 0.35rem; border-radius: 0.2rem; font-weight: bold;">HD</span>
                <span style="background: #2a9d8f; color:#fff; font-size: 0.65rem; padding: 0.15rem 0.35rem; border-radius: 0.2rem; font-weight: bold;">CC ${anime.sub_episodes || 1}</span>
                ${anime.dub_episodes ? `<span style="background: #457b9d; color:#fff; font-size: 0.65rem; padding: 0.15rem 0.35rem; border-radius: 0.2rem; font-weight: bold;">🎙️ ${anime.dub_episodes}</span>` : ""}
                <span style="background: rgba(255,255,255,0.05); color:#fff; font-size: 0.65rem; padding: 0.15rem 0.35rem; border-radius: 0.2rem;">${anime.type}</span>
              </div>
            </div>
          </div>
          <p style="font-size: 0.8rem; line-height: 1.5; color: var(--muted); margin: 0; display: -webkit-box; -webkit-line-clamp: 6; -webkit-box-orient: vertical; overflow: hidden;" title="${anime.description}">
            ${anime.description}
          </p>
          <a href="#/anime/${anime.id}" class="search-submit-btn" style="height: auto; padding: 0.5rem 1rem; font-size: 0.8rem; font-weight: bold; border: none; width: 100%; border-radius: 0.35rem; text-decoration: none; text-align: center; display: block;">
            View detail
          </a>
        </div>
      </div>

      <!-- Bottom Layout Section -->
      <div class="hianime-bottom-row">
        <!-- Bottom Left: Comments & Recommendations -->
        <div style="display: flex; flex-direction: column; gap: 1.5rem; min-width: 0;">
          <!-- Social Share Bar mimicking HiAnime -->
          <div style="display: flex; align-items: center; gap: 1rem; background: rgba(17, 22, 26, 0.4); border: 1px solid var(--border); padding: 0.75rem 1.25rem; border-radius: 0.5rem; flex-wrap: wrap;">
            <div style="display:flex; gap:0.5rem; align-items:center;">
              <img src="${anime.poster}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;" />
              <span style="font-size:0.85rem; color:#fff; font-weight:bold;">Share Nompyr</span>
              <span style="font-size:0.75rem; color:var(--muted);">to your friends</span>
            </div>
            <div style="display:flex; gap:0.5rem; margin-left:auto; flex-wrap:wrap;">
              <button class="button" style="background:#0088cc; color:#fff; font-size:0.75rem; height:auto; padding:0.4rem 0.8rem; border:none; border-radius:0.25rem;">Share Telegram</button>
              <button class="button" style="background:#1da1f2; color:#fff; font-size:0.75rem; height:auto; padding:0.4rem 0.8rem; border:none; border-radius:0.25rem;">Post Twitter</button>
              <button class="button" style="background:#3b5998; color:#fff; font-size:0.75rem; height:auto; padding:0.4rem 0.8rem; border:none; border-radius:0.25rem;">Share Facebook</button>
              <button class="button" style="background:#ff4500; color:#fff; font-size:0.75rem; height:auto; padding:0.4rem 0.8rem; border:none; border-radius:0.25rem;">Share Reddit</button>
            </div>
          </div>

          <!-- Comments Panel -->
          <div class="hianime-comments-panel">
            <h2 style="margin-top:0; margin-bottom:1.25rem; font-size:1.15rem; color:#fff; display:flex; align-items:center; gap:0.5rem;">
              Comments <span style="font-size: 0.75rem; font-weight: normal; background: rgba(255,255,255,0.08); padding: 0.15rem 0.5rem; border-radius: 0.2rem; color: var(--muted);">Guest Mode</span>
            </h2>
            <form id="commentForm" style="display:flex; flex-direction:column; gap:0.75rem; margin-bottom:1.5rem;">
              <div style="display:flex; gap:0.5rem;">
                <input type="text" id="commentUser" placeholder="Your name..." required style="padding: 0.6rem 0.8rem; background: rgba(0,0,0,0.25); border: 1px solid var(--border); border-radius: 0.35rem; color: #fff; font-size: 0.85rem; width: 200px; outline:none;" />
              </div>
              <textarea id="commentText" placeholder="Leave a comment..." required style="padding: 0.6rem 0.8rem; background: rgba(0,0,0,0.25); border: 1px solid var(--border); border-radius: 0.35rem; color: #fff; font-size: 0.85rem; height: 4.5rem; resize: none; outline:none;"></textarea>
              <button type="submit" class="search-submit-btn" style="height: auto; padding: 0.5rem 1.5rem; font-size: 0.85rem; align-self: flex-end; width: auto; font-weight:600; border:none; border-radius:0.35rem;">Comment</button>
            </form>
            <div id="commentsList" style="display:flex; flex-direction:column; gap:0.75rem; padding-right: 0.25rem;">
               <!-- Comments dynamically loaded -->
            </div>
          </div>

          <!-- Recommendations Panel (dynamically resolved) -->
          <div id="watchRecommendationsContainer" style="margin-top:0.5rem;">
            <div style="padding: 2rem; text-align: center; color: var(--muted); font-size: 0.9rem; background: rgba(17, 22, 26, 0.85); border: 1px solid var(--border); border-radius: 0.65rem;">
              Loading recommendations...
            </div>
          </div>
        </div>

        <!-- Bottom Right: Most Popular -->
        <div class="hianime-popular-sidebar">
          <h2 style="margin: 0 0 0.5rem 0; font-size: 1.1rem; color: #fff; font-weight: bold;">Most Popular</h2>
          <div class="hianime-popular-list">
            ${popularItems.map((item) => `
              <a href="#/anime/${item.id}" class="hianime-popular-item">
                <img src="${item.poster}" />
                <div class="hianime-popular-info">
                  <div class="hianime-popular-title" title="${item.title}">${item.title}</div>
                  <div class="hianime-popular-meta">
                    <span style="background: rgba(255,255,255,0.05); color: var(--muted); font-size: 0.65rem; padding: 0.1rem 0.3rem; border-radius: 0.15rem; font-weight: bold;">CC ${item.sub_episodes || item.episodes || 1}</span>
                    ${item.dub_episodes ? `<span style="background: rgba(124,58,237,0.15); color: #c084fc; font-size: 0.65rem; padding: 0.1rem 0.3rem; border-radius: 0.15rem; font-weight: bold;">🎙️ ${item.dub_episodes}</span>` : ""}
                    <span style="font-size: 0.7rem; color: var(--muted); margin-left: 0.25rem;">${item.type || "TV"}</span>
                  </div>
                </div>
              </a>
            `).join("")}
          </div>
        </div>
      </div>
    </div>
  `;

  // Start loading recommendations in background
  const recsContainer = document.getElementById("watchRecommendationsContainer");
  if (recsContainer) {
    loadWatchRecommendations(anime, recsContainer);
  }

  // Setup comments list & form
  const renderComments = () => {
    const commentsList = document.getElementById("commentsList");
    if (!commentsList) return;

    const list = getCommentsForAnime(anime.id, anime.title);
    if (list.length === 0) {
      commentsList.innerHTML = `<p class="muted" style="font-size:0.85rem; text-align:center; padding:1.5rem 0;">No comments yet. Be the first to post!</p>`;
      return;
    }

    commentsList.innerHTML = list.map(c => `
      <div class="comment-item" style="padding: 0.75rem 1rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); border-radius: 0.5rem; display: flex; gap: 0.75rem; align-items: flex-start;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: #e76f51; color: #fff; font-size: 0.95rem; font-weight: bold; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
          ${(c.user || "G").charAt(0).toUpperCase()}
        </div>
        <div style="flex-grow: 1; min-width: 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
            <strong style="color:#e76f51; font-size:0.85rem;">${c.user}</strong>
            <span style="font-size:0.75rem; color:var(--muted);">${c.date || "Just now"}</span>
          </div>
          <p style="margin:0; font-size:0.85rem; line-height:1.4; color:rgba(255,255,255,0.8);">${c.text}</p>
        </div>
      </div>
    `).join("");
  };

  renderComments();

  document.getElementById("commentForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const userEl = document.getElementById("commentUser");
    const textEl = document.getElementById("commentText");
    if (!userEl || !textEl) return;

    const newComment = {
      user: userEl.value.trim(),
      text: textEl.value.trim(),
      date: "Just now"
    };

    saveComment(anime.id, newComment);
    textEl.value = "";
    showToast("Comment posted!");
    renderComments();
  });

  // Setup episodes search filter
  const epSearchInput = document.getElementById("epSearchInput");
  epSearchInput?.addEventListener("input", (e) => {
    const term = e.target.value.trim().toLowerCase();
    const links = document.querySelectorAll(".ep-link-item");
    links.forEach(link => {
      const epNum = link.getAttribute("data-ep-num") || "";
      const epText = link.textContent.toLowerCase();
      if (!term || epNum === term || epText.includes(term)) {
        link.style.display = "flex";
      } else {
        link.style.display = "none";
      }
    });
  });

  // Setup micro-actions listeners in controls bar
  document.getElementById("actionExpand")?.addEventListener("click", () => {
    const player = document.querySelector(".player");
    if (player) {
      player.classList.toggle("theatre");
      showToast("Expanded/collapsed player layout");
    }
  });

  document.getElementById("actionLight")?.addEventListener("click", (e) => {
    const body = document.body;
    const isOff = body.style.background === "rgb(0, 0, 0)";
    if (isOff) {
      body.style.background = "";
      e.target.innerHTML = "💡 Light <strong>On</strong>";
      showToast("Lights turned on");
    } else {
      body.style.background = "#000";
      e.target.innerHTML = "💡 Light <strong>Off</strong>";
      showToast("Lights dimmed");
    }
  });

  document.getElementById("actionAutoplay")?.addEventListener("click", (e) => {
    const current = store.getState().settings.autoplay;
    store.updateSetting("autoplay", !current);
    e.target.innerHTML = `🔄 Auto Play <strong>${!current ? "On" : "Off"}</strong>`;
    showToast(`Autoplay ${!current ? "enabled" : "disabled"}`);
  });

  document.getElementById("actionAutonext")?.addEventListener("click", (e) => {
    const current = store.getState().settings.autoplay;
    store.updateSetting("autoplay", !current);
    e.target.innerHTML = `⏭️ Auto Next <strong>${!current ? "On" : "Off"}</strong>`;
    showToast(`Auto Next ${!current ? "enabled" : "disabled"}`);
  });

  document.getElementById("actionAutoSkip")?.addEventListener("click", (e) => {
    const current = store.getState().settings.skipIntro;
    store.updateSetting("skipIntro", !current);
    e.target.innerHTML = `⏩ Auto Skip Intro <strong>${!current ? "On" : "Off"}</strong>`;
    showToast(`Auto skip intro ${!current ? "enabled" : "disabled"}`);
  });

  document.querySelector("#simulateProgress")?.addEventListener("click", () => {
    const next = Math.min(100, progress + 18 || 18);
    store.addHistory({
      animeId: anime.id,
      episodeId: episode.id,
      title: anime.title,
      episode: episode.number,
      progress: next,
      date: new Date().toISOString()
    });
    showToast(`Saved ${next}% progress`);
    renderWatch(slug, episodeNo);
  });

  // Setup Hls.js or Native Player
  const video = document.getElementById("videoPlayer");
  if (video) {
    let lastSaveTime = 0;
    const autoplay = store.getState().settings.autoplay;
    const skipIntroSetting = store.getState().settings.skipIntro;
    const skipOutroSetting = store.getState().settings.skipOutro;

    const fallbackToIframe = () => {
      const playerContainer = video.parentElement;
      if (playerContainer && (stream.embed_url || stream.embedUrl)) {
        cleanupHls();
        playerContainer.innerHTML = `<iframe src="${stream.embed_url || stream.embedUrl}" class="video-player" allow="autoplay; fullscreen" sandbox="allow-scripts allow-same-origin allow-forms" style="width:100%;height:100%;border:none;"></iframe>`;
        showToast("Direct stream unavailable. Switched to embed player.");
      }
    };

    // Watchdog timer to detect stalls (e.g. CORS block, 403, or loading hangs)
    const startWatchdog = () => {
      if (state.watchdog) clearTimeout(state.watchdog);
      state.watchdog = setTimeout(() => {
        if (video && video.currentTime === 0) {
          console.warn("Watchdog: Playback did not start within 6 seconds. Falling back to iframe.");
          fallbackToIframe();
        }
      }, 6000);
    };

    video.addEventListener("play", startWatchdog);

    video.addEventListener("playing", () => {
      if (state.watchdog) {
        clearTimeout(state.watchdog);
        state.watchdog = null;
      }
    });

    video.addEventListener("error", (e) => {
      console.error("Native video error:", e);
      fallbackToIframe();
    });

    const isDirectMp4 = stream.type === "mp4" || stream.hls.split('?')[0].toLowerCase().endsWith(".mp4") || stream.hls.toLowerCase().includes(".mp4");
    if (isDirectMp4) {
      video.src = stream.hls;
    } else if (Hls.isSupported() && stream.hls) {
      const hls = new Hls();
      hls.loadSource(stream.hls);
      hls.attachMedia(video);
      state.videoHlsInstance = hls;

      hls.on(Hls.Events.ERROR, function (event, data) {
        console.warn("HLS.js error:", data);
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error("Fatal network error in HLS playback. Falling back to iframe.");
              fallbackToIframe();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.warn("Fatal media error, trying to recover...");
              hls.recoverMediaError();
              break;
            default:
              console.error("Fatal HLS error. Falling back to iframe.");
              fallbackToIframe();
              break;
          }
        }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl') && stream.hls) {
      video.src = stream.hls;
    }

    video.addEventListener("loadedmetadata", () => {
      const savedProgress = store.getState().progress[episode.id];
      if (savedProgress && savedProgress > 0 && savedProgress < 98) {
        const resumeTime = (savedProgress / 100) * video.duration;
        video.currentTime = resumeTime;
        showToast(`Resumed from ${Math.floor(savedProgress)}% (${formatTime(resumeTime)})`);
      }
      if (autoplay) {
        video.play().catch(e => console.log("Autoplay blocked:", e));
      }
    });

    video.addEventListener("timeupdate", () => {
      const currentTime = video.currentTime;
      const duration = video.duration;
      if (!duration) return;

      // History Progress Saving
      if (Math.abs(currentTime - lastSaveTime) > 5) {
        lastSaveTime = currentTime;
        store.addHistory({
          animeId: anime.id,
          episodeId: episode.id,
          title: anime.title,
          episode: episode.number,
          progress: Math.min(100, Math.floor((currentTime / duration) * 100)),
          date: new Date().toISOString()
        });
      }

      // Skip Overlay handling
      const overlay = document.getElementById("playerOverlay");
      if (overlay) {
        const intro = stream.intro || [0, 0];
        const outro = stream.outro || [0, 0];

        if (intro[0] > 0 && intro[1] > intro[0] && currentTime >= intro[0] && currentTime <= intro[1]) {
          if (skipIntroSetting) {
            video.currentTime = intro[1];
            showToast("Skipped intro automatically");
            overlay.innerHTML = "";
            return;
          }
          if (!document.getElementById("skipIntroBtn")) {
            overlay.innerHTML = `<button class="skip-overlay-btn" id="skipIntroBtn">Skip Intro ›</button>`;
            document.getElementById("skipIntroBtn")?.addEventListener("click", () => {
              video.currentTime = intro[1];
              showToast("Skipped intro");
              overlay.innerHTML = "";
            });
          }
        } else if (outro[0] > 0 && outro[1] > outro[0] && currentTime >= outro[0] && currentTime <= outro[1]) {
          if (skipOutroSetting) {
            video.currentTime = outro[1];
            showToast("Skipped outro automatically");
            overlay.innerHTML = "";
            return;
          }
          if (!document.getElementById("skipOutroBtn")) {
            overlay.innerHTML = `<button class="skip-overlay-btn" id="skipOutroBtn">Skip Outro ›</button>`;
            document.getElementById("skipOutroBtn")?.addEventListener("click", () => {
              video.currentTime = outro[1];
              showToast("Skipped outro");
              overlay.innerHTML = "";
            });
          }
        } else {
          overlay.innerHTML = "";
        }
      }
    });

    video.addEventListener("ended", () => {
      store.addHistory({
        animeId: anime.id,
        episodeId: episode.id,
        title: anime.title,
        episode: episode.number,
        progress: 100,
        date: new Date().toISOString()
      });
      const nextEp = episodes.find((item) => Number(item.number) === Number(episode.number) + 1);
      if (nextEp && nextEp.released) {
        showToast(`Autoplay: Loading Episode ${nextEp.number}...`);
        setTimeout(() => {
          location.hash = `#/watch/${anime.id}/${nextEp.number}`;
        }, 1500);
      } else {
        showToast("Completed the last available episode!");
      }
    });
  }
};

const renderSchedule = async () => {
  const schedule = await sourceManager.schedule();
  view.innerHTML = `
    <div class="page-head"><span>Weekly release board</span><h1>Schedule</h1></div>
    <div class="schedule-grid">
      ${schedule.map((day) => `
        <section class="panel day-panel">
          <h2>${day.day}</h2>
          ${day.releases.length ? day.releases.map((item) => {
            const isHanime = String(item.id).startsWith("hanime:");
            const targetHash = isHanime 
              ? `https://hanime.tv/videos/hentai/${item.id.split("hanime:")[1]}` 
              : `#/anime/${item.id}`;
            const targetAttr = isHanime ? 'target="_blank" rel="noopener noreferrer"' : '';
            return `<a href="${targetHash}" ${targetAttr}><strong>${item.title}</strong><span>Episode ${item.latestEpisode || 1}</span></a>`;
          }).join("") : `<p class="muted">No releases listed.</p>`}
        </section>
      `).join("")}
    </div>
  `;
};

const renderSaved = (kind) => {
  const stateNow = store.getState();
  const items =
    kind === "favorites"
      ? animeCatalog.filter((anime) => stateNow.favorites.includes(anime.id))
      : stateNow.history.map((entry) => ({ entry, anime: animeCatalog.find((anime) => anime.id === entry.animeId) })).filter((item) => item.anime);

  view.innerHTML = `
    <div class="page-head"><span>${items.length} saved</span><h1>${kind === "favorites" ? "Favorites" : "Watch History"}</h1></div>
    ${
      kind === "favorites"
        ? `<div class="grid">${items.map((item) => card(item)).join("") || `<div class="empty">No favorites yet.</div>`}</div>`
        : `<div class="history-list">${items.map(({ entry, anime }) => {
            const isHanime = String(anime.id).startsWith("hanime:");
            const targetHash = isHanime 
              ? `https://hanime.tv/videos/hentai/${anime.id.split("hanime:")[1]}` 
              : `#/watch/${anime.id}/${entry.episode}`;
            const targetAttr = isHanime ? 'target="_blank" rel="noopener noreferrer"' : '';
            return `<a href="${targetHash}" ${targetAttr}>${card(anime, true)}<span>${entry.progress}% watched</span></a>`;
          }).join("") || `<div class="empty">No history yet.</div>`}</div><button class="button ghost" id="clearHistory">Clear History</button>`
    }
  `;
  document.querySelector("#clearHistory")?.addEventListener("click", () => {
    store.clearHistory();
    renderSaved("history");
  });
};

const renderProfile = () => {
  const current = store.getState();
  view.innerHTML = `
    <div class="page-head"><span>Local guest mode</span><h1>Profile</h1></div>
    <div class="settings-grid">
      ${Object.entries(current.settings).map(([name, value]) => `
        <label class="setting-card">
          <span><strong>${name.replace(/[A-Z]/g, " $&")}</strong><small>${value ? "Enabled" : "Disabled"}</small></span>
          <input type="checkbox" data-setting="${name}" ${value ? "checked" : ""} />
        </label>
      `).join("")}
    </div>
  `;
};

const renderAdmin = () => {
  const current = store.getState();
  const api = sourceManager.apiStatus();
  view.innerHTML = `
    <div class="page-head"><span>Source and product overview</span><h1>Admin Dashboard</h1></div>
    <div class="admin-grid">
      <section class="metric"><span>${animeCatalog.length}</span><p>Anime indexed</p></section>
      <section class="metric"><span>${current.history.length}</span><p>History events</p></section>
      <section class="metric"><span>${current.favorites.length}</span><p>Favorites</p></section>
      <section class="metric"><span>98%</span><p>Cache hit target</p></section>
    </div>
    <section class="panel">
      <div class="section-head"><h2>Data API</h2><span>${api.contentReady ? "Active" : "Demo fallback"}</span></div>
      <div class="source-table">
        <div><strong>Provider</strong><span>${api.provider}</span><small>${api.contentReady ? "Content source enabled" : "Missing URL"}</small></div>
        <div><strong>Base URL</strong><span>${api.baseUrl}</span><small>${api.configured ? "Key configured" : "No key stored"}</small></div>
        <div><strong>Auth Headers</strong><span>x-api-key + Bearer</span><small>Frontend storage only</small></div>
      </div>
      <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.05);">
        <button id="resetApiConfigBtn" class="search-submit-btn" style="height: auto; padding: 0.6rem 1.5rem; font-size: 0.8rem;">
          RESET API TO DEFAULT
        </button>
      </div>
    </section>
    <section class="panel">
      <div class="section-head"><h2>Source Health</h2><span>Demo adapter</span></div>
      <div class="source-table">
        ${animeCatalog.map((anime) => `<div><strong>${anime.title}</strong><span>${anime.sourceHealth}</span><small>${anime.updatedAt}</small></div>`).join("")}
      </div>
    </section>
  `;
};

const render = async () => {
  if (state.clockInterval) {
    clearInterval(state.clockInterval);
    state.clockInterval = null;
  }
  cleanupHls();
  setActive();
  rail.classList.remove("open");
  const { page, parts } = route();

  if (parts[0] && String(parts[0]).startsWith("hanime:")) {
    const slug = parts[0].split("hanime:")[1];
    window.location.replace(`https://hanime.tv/videos/hentai/${slug}`);
    return;
  }

  view.innerHTML = `<div class="loading">Loading Nompyr...</div>`;
  try {
    if (page === "home") await renderHome();
    else if (page === "search") await renderSearch();
    else if (["trending", "latest", "popular"].includes(page)) await renderCollection(page);
    else if (page === "anime") await renderAnime(parts[0]);
    else if (page === "watch") await renderWatch(parts[0], parts[1]);
    else if (page === "schedule") await renderSchedule();
    else if (page === "favorites" || page === "history") renderSaved(page);
    else if (page === "profile") renderProfile();
    else if (page === "admin") renderAdmin();
    else if (page === "recommender") await renderRecommendations();
    else await renderHome();
  } catch (error) {
    const api = sourceManager.apiStatus();
    view.innerHTML = `
      <div class="empty-state" style="max-width: 36rem; margin: 5rem auto; text-align: center; padding: 3rem 2rem; border: 1px solid var(--border); border-radius: 1rem; background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);">
        <div class="empty-icon" style="font-size: 3.5rem; margin-bottom: 1.5rem; color: #E76F51; filter: drop-shadow(0 4px 10px rgba(231, 111, 81, 0.2));">⚠️</div>
        <h2 style="margin-bottom: 0.75rem; color: #fff; font-size: 1.6rem; font-weight: 750;">Unable to Load Content</h2>
        <p style="color: var(--muted); margin-bottom: 2rem; font-size: 0.95rem; line-height: 1.6; max-width: 28rem; margin-left: auto; margin-right: auto;">
          ${error.message.replace(/;/g, '<br>')}
        </p>
        <div style="display: flex; flex-direction: column; gap: 0.75rem; align-items: center; justify-content: center;">
          <a href="#/" class="search-submit-btn" style="display: inline-flex; text-decoration: none; font-size: 0.85rem; padding: 0.75rem 2rem; height: auto;">
            RETURN TO HOME
          </a>
          ${!window.location.origin.includes("127.0.0.1") && !window.location.origin.includes("localhost") && !window.location.origin.includes("4173") ? `
            <button id="errorUseLocalApiBtn" class="search-submit-btn" style="display: inline-flex; height: auto; padding: 0.75rem 2rem; font-size: 0.85rem; background: #e76f51; color: #fff; border: none; font-weight: bold; box-shadow: 0 4px 14px rgba(231, 111, 81, 0.3);">
              CONNECT TO LOCAL BACKEND (127.0.0.1:5000)
            </button>
          ` : ''}
          ${api.contentReady ? `
            <button id="errorResetApiBtn" class="search-submit-btn" style="display: inline-flex; height: auto; padding: 0.75rem 2rem; font-size: 0.85rem; background: rgba(255, 255, 255, 0.08); color: #fff; border: 1px solid var(--border); box-shadow: none;">
              RESET API TO DEFAULT
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }
};

document.addEventListener("click", async (event) => {
  const errorResetBtn = event.target.closest("#errorResetApiBtn");
  if (errorResetBtn) {
    store.clearApiConfig();
    showToast("API configuration reset to default!");
    location.hash = "#/";
    render();
    return;
  }

  const useLocalApiBtn = event.target.closest("#errorUseLocalApiBtn");
  if (useLocalApiBtn) {
    store.updateApiConfig({
      enabled: true,
      provider: "all",
      baseUrl: "http://127.0.0.1:5000",
      key: ""
    });
    showToast("Connected to local backend on 127.0.0.1:5000!");
    location.hash = "#/";
    render();
    return;
  }

  const resetApiBtn = event.target.closest("#resetApiConfigBtn");
  if (resetApiBtn) {
    store.clearApiConfig();
    showToast("API configuration reset to default!");
    renderAdmin();
    return;
  }

  const calDayBtn = event.target.closest("[data-calendar-day]");
  if (calDayBtn) {
    state.selectedCalendarDay = calDayBtn.dataset.calendarDay;
    renderHome();
    return;
  }

  const calExpandBtn = event.target.closest("#calendarExpandBtn");
  if (calExpandBtn) {
    location.hash = "#/schedule";
    return;
  }

  const homeFilterBtn = event.target.closest("[data-home-filter]");
  if (homeFilterBtn) {
    state.homeFilter = homeFilterBtn.dataset.homeFilter;
    renderHome();
    return;
  }

  const azChipBtn = event.target.closest("[data-az-chip]");
  if (azChipBtn) {
    const char = azChipBtn.dataset.azChip;
    state.filters.az = char === "All" ? "" : char;
    state.filters.page = 1;
    location.hash = "#/search";
    renderSearch();
    return;
  }

  const favorite = event.target.closest("[data-favorite]");
  const hero = event.target.closest("[data-hero]");
  const download = event.target.closest("[data-download]");
  const serverBtn = event.target.closest("[data-server-id]");
  const langTab = event.target.closest("[data-lang]");
  const theatreBtn = event.target.closest("[data-theatre]");
  const pipBtn = event.target.closest("[data-pip]");
  const fullscreenBtn = event.target.closest("[data-fullscreen]");
  const chipBtn = event.target.closest(".chip-btn");

  if (favorite) {
    const enabled = store.toggleFavorite(favorite.dataset.favorite);
    showToast(enabled ? "Added to favorites" : "Removed from favorites");
    render();
  }

  if (hero) {
    state.heroIndex = Number(hero.dataset.hero);
    renderHome();
  }

  if (download) {
    const result = await sourceManager.download(download.dataset.download, "720p");
    showToast(result.message);
    if (result.url) {
      window.open(result.url, "_blank");
    }
  }

  if (serverBtn) {
    state.activeServerId = serverBtn.dataset.serverId;
    if (serverBtn.dataset.mode) {
      state.activeLanguage = serverBtn.dataset.mode;
    }
    const { parts } = route();
    renderWatch(parts[0], parts[1]);
  }

  if (langTab) {
    state.activeLanguage = langTab.dataset.lang;
    state.activeServerId = null;
    const { parts } = route();
    renderWatch(parts[0], parts[1]);
  }

  if (theatreBtn) {
    const player = document.querySelector(".player");
    if (player) {
      const isTheatreNow = !player.classList.contains("theatre");
      player.classList.toggle("theatre", isTheatreNow);
      store.updateSetting("theatre", isTheatreNow);
      showToast(isTheatreNow ? "Theatre mode enabled" : "Theatre mode disabled");
    }
  }

  if (pipBtn) {
    const video = document.getElementById("videoPlayer");
    if (video) {
      if (document.pictureInPictureElement) {
        document.exitPictureInPicture().catch(() => {});
      } else {
        video.requestPictureInPicture().catch(() => {});
      }
    }
  }

  if (fullscreenBtn) {
    const video = document.getElementById("videoPlayer");
    if (video) {
      if (!document.fullscreenElement) {
        video.requestFullscreen?.() || video.webkitRequestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
    }
  }

  if (chipBtn) {
    const query = chipBtn.dataset.search;
    state.filters.query = query;
    const sInput = document.querySelector("#searchInput");
    const lSearch = document.querySelector("#localSearch");
    if (sInput) sInput.value = query;
    if (lSearch) lSearch.value = query;
    renderSearch();
  }

  const heroNav = event.target.closest("[data-hero-nav]");
  if (heroNav) {
    const dir = heroNav.dataset.heroNav;
    const data = await sourceManager.home();
    const len = data.spotlight.length || 4;
    if (dir === "next") {
      state.heroIndex = (state.heroIndex + 1) % len;
    } else {
      state.heroIndex = (state.heroIndex - 1 + len) % len;
    }
    renderHome();
  }

  const randomBtn = event.target.closest("#randomAnimeBtn");
  if (randomBtn) {
    if (animeCatalog && animeCatalog.length) {
      const idx = Math.floor(Math.random() * animeCatalog.length);
      location.hash = `#/watch/${animeCatalog[idx].id}/1`;
    }
  }

  const shareCopy = event.target.closest("#shareCopyLinkBtn");
  if (shareCopy) {
    navigator.clipboard.writeText(location.origin + location.pathname).then(() => {
      showToast("Link copied to clipboard!");
    }).catch(() => {
      showToast("Failed to copy link.");
    });
  }

  const pagBtn = event.target.closest("[data-pag]");
  if (pagBtn) {
    const dir = pagBtn.dataset.pag;
    if (dir === "next") {
      state.filters.page = (state.filters.page || 1) + 1;
    } else if (dir === "prev") {
      state.filters.page = Math.max(1, (state.filters.page || 1) - 1);
    }
    renderSearch();
  }

  const genreChip = event.target.closest("[data-genre-chip]");
  if (genreChip) {
    const g = genreChip.dataset.genreChip;
    if (!state.filters.genres) state.filters.genres = [];
    if (state.filters.genres.includes(g)) {
      state.filters.genres = state.filters.genres.filter(item => item !== g);
    } else {
      state.filters.genres.push(g);
    }
    state.filters.page = 1;
    renderSearch();
  }

  const resetBtn = event.target.closest("#resetFiltersBtn");
  if (resetBtn) {
    state.filters = {
      query: "",
      genres: [],
      type: "",
      status: "",
      rating: "",
      score: "",
      season: "",
      language: "",
      startYear: "",
      startMonth: "",
      startDay: "",
      endYear: "",
      endMonth: "",
      endDay: "",
      sort: "score_desc",
      page: 1
    };
    const sInput = document.querySelector("#searchInput");
    if (sInput) sInput.value = "";
    renderSearch();
  }

  const recTab = event.target.closest("[data-rec-tab]");
  if (recTab) {
    state.recommenderTab = recTab.dataset.recTab;
    state.recommenderResults = [];
    state.recTriggered = false;
    renderRecommendations();
  }
});

document.addEventListener("input", (event) => {
  const map = {
    localSearch: "query",
    typeFilter: "type",
    statusFilter: "status",
    ratingFilter: "rating",
    scoreFilter: "score",
    seasonFilter: "season",
    languageFilter: "language",
    startYearFilter: "startYear",
    startMonthFilter: "startMonth",
    startDayFilter: "startDay",
    endYearFilter: "endYear",
    endMonthFilter: "endMonth",
    endDayFilter: "endDay",
    sortFilter: "sort"
  };

  if (map[event.target.id]) {
    state.filters[map[event.target.id]] = event.target.value;
    state.filters.page = 1;
    
    if (event.target.id === "localSearch") {
      setupAutocomplete(event.target, document.querySelector("#localSearchSuggestions"));
      if (state.searchTimeout) clearTimeout(state.searchTimeout);
      state.searchTimeout = setTimeout(() => {
        renderSearch();
      }, 400);
    } else {
      renderSearch();
    }
  }

  if (event.target.dataset.setting) {
    store.updateSetting(event.target.dataset.setting, event.target.checked);
    renderProfile();
  }
});

globalSearch.addEventListener("submit", (event) => {
  event.preventDefault();
  const dropdown = document.querySelector("#searchSuggestions");
  if (dropdown) dropdown.classList.add("hidden");
  state.filters.query = searchInput.value.trim();
  state.filters.page = 1;
  location.hash = "#/search";
  renderSearch();
});

menuToggle.addEventListener("click", (event) => {
  event.stopPropagation();
  const popupNav = document.getElementById("popupNav");
  if (popupNav) {
    popupNav.classList.toggle("hidden");
  }
});

const popupNavEl = document.getElementById("popupNav");
if (popupNavEl) {
  popupNavEl.addEventListener("mouseleave", () => {
    popupNavEl.classList.add("hidden");
  });
}
document.querySelector("#themeToggle")?.addEventListener("click", () => document.body.classList.toggle("high-contrast"));
window.addEventListener("hashchange", render);

setInterval(() => {
  if (route().page === "home") {
    state.heroIndex = (state.heroIndex + 1) % 4;
    renderHome();
  }
}, 9000);

const setupAutocomplete = (input, dropdown, isRecommenderPage = false) => {
  const q = input.value.trim();
  if (q.length < 2) {
    dropdown.innerHTML = "";
    dropdown.classList.add("hidden");
    return;
  }

  if (input.dataset.timeoutId) clearTimeout(Number(input.dataset.timeoutId));

  const timeoutId = setTimeout(async () => {
    try {
      let suggestions = [];
      try {
        const api = store.getState().api || {};
        const baseUrl = api.baseUrl || "http://127.0.0.1:5000";
        const res = await fetch(`${baseUrl}/api/search-predictions?q=${encodeURIComponent(input.value.trim())}`);
        if (res.ok) {
          suggestions = await res.json();
        } else {
          throw new Error("Backend responded with error status");
        }
      } catch (err) {
        console.warn("Backend autocomplete query failed, trying direct Jikan fetch:", err);
        const res = await fetch(`https://api.jikan.moe/v4/anime?q=${encodeURIComponent(input.value.trim())}&limit=6`);
        if (res.ok) {
          const payload = await res.json();
          suggestions = (payload.data || []).map(item => ({
            title: item.title,
            poster: item.images?.jpg?.small_image_url || item.images?.jpg?.image_url || "",
            id: `jikan:${item.mal_id}`
          }));
        }
      }

      if (suggestions && suggestions.length > 0) {
        dropdown.innerHTML = suggestions.map((item, idx) => {
          const title = typeof item === 'string' ? item : item.title;
          const poster = typeof item === 'object' && item.poster ? item.poster : '';
          return `
            <div class="suggestion-item" data-index="${idx}" data-val="${title.replace(/"/g, '&quot;')}">
              ${poster ? `<img src="${poster}" />` : ''}
              <span>${title}</span>
            </div>
          `;
        }).join("");
        dropdown.classList.remove("hidden");
      } else {
        dropdown.innerHTML = "";
        dropdown.classList.add("hidden");
      }
    } catch (err) {
      console.warn("Autocomplete fetch error", err);
    }
  }, 180);

  input.dataset.timeoutId = String(timeoutId);

  if (!dropdown.dataset.clickBound) {
    dropdown.dataset.clickBound = "true";
    dropdown.addEventListener("click", (e) => {
      const item = e.target.closest(".suggestion-item");
      if (item) {
        const val = item.dataset.val;
        input.value = val;
        dropdown.innerHTML = "";
        dropdown.classList.add("hidden");
        if (isRecommenderPage) {
          if (input.id === "recAnimeInput") {
            state.recommenderAnimeTitle = val;
            const btn = document.getElementById("getAnimeRecsBtn");
            if (btn) btn.disabled = false;
          }
        } else {
          state.filters.query = val;
          const sInput = document.querySelector("#searchInput");
          const lSearch = document.querySelector("#localSearch");
          if (sInput) sInput.value = val;
          if (lSearch) lSearch.value = val;
          state.filters.page = 1;
          location.hash = "#/search";
          renderSearch();
        }
      }
    });
  }
};

// Global click-away handler for autocomplete dropdowns and popup navigation
document.addEventListener("click", (e) => {
  const dropdowns = document.querySelectorAll(".search-suggestions-dropdown");
  dropdowns.forEach(dropdown => {
    const wrap = dropdown.parentElement;
    if (wrap && !wrap.contains(e.target)) {
      dropdown.classList.add("hidden");
    }
  });

  const popupNav = document.getElementById("popupNav");
  if (popupNav && !popupNav.contains(e.target) && e.target.id !== "menuToggle") {
    popupNav.classList.add("hidden");
  }
});

const renderRecommendations = async () => {
  if (!state.recommenderTab) state.recommenderTab = "description";
  if (!state.recommenderResults) state.recommenderResults = [];
  if (!state.recommenderQuery) state.recommenderQuery = "";
  if (!state.recommenderAnimeTitle) state.recommenderAnimeTitle = "";

  const results = state.recommenderResults;
  const activeTab = state.recommenderTab;

  view.innerHTML = `
    <div class="recommender-container" style="max-width: 80rem; margin: 0 auto; padding: 2rem clamp(1rem, 3vw, 2rem);">
      <div class="page-head">
        <span>AI & Community Recommender</span>
        <h1>Anime Discoverer</h1>
      </div>

      <div class="recommender-card">
        <p class="recommender-description">
          Welcome to the Advanced Recommendation Engine. Choose between describing your ideal anime mood/plot to match using local TF-IDF semantic metrics, or type an anime title to fetch community fallbacks via MAL/Jikan API.
        </p>

        <div class="recommender-tabs">
          <button class="recommender-tab-btn ${activeTab === "description" ? "active" : ""}" data-rec-tab="description">Plot Description Match</button>
          <button class="recommender-tab-btn ${activeTab === "anime" ? "active" : ""}" data-rec-tab="anime">Anime Relationship Match</button>
        </div>

        <!-- Description Tab Panel -->
        <div class="recommender-tab-panel ${activeTab === "description" ? "" : "hidden"}">
          <div class="recommender-input-group">
            <label for="recDescInput">What plot elements or mood are you looking for?</label>
            <textarea id="recDescInput" class="recommender-textarea" placeholder="E.g., A psychological mystery or thriller with smart characters who outwit each other, like Death Note or Monster...">${state.recommenderQuery}</textarea>
          </div>
          <button class="recommender-btn" id="getDescRecsBtn" ${!state.recommenderQuery.trim() ? "disabled" : ""}>
            <span>✦ Get Recommendations</span>
          </button>
        </div>

        <!-- Anime Tab Panel -->
        <div class="recommender-tab-panel ${activeTab === "anime" ? "" : "hidden"}">
          <div class="recommender-input-group">
            <label for="recAnimeInput">Search anime by title to find related titles:</label>
            <div style="position:relative;width:100%;">
              <input id="recAnimeInput" type="text" placeholder="E.g., Jujutsu Kaisen..." value="${state.recommenderAnimeTitle}" autocomplete="off" style="width:100%;" />
              <div id="recAnimeSuggestions" class="search-suggestions-dropdown hidden"></div>
            </div>
          </div>
          <button class="recommender-btn" id="getAnimeRecsBtn" ${!state.recommenderAnimeTitle.trim() ? "disabled" : ""}>
            <span>✦ Get Recommendations</span>
          </button>
        </div>
      </div>

      <!-- Results Grid -->
      ${state.recLoading ? `
        <div class="loading">Analyzing catalog and searching recommendations...</div>
      ` : results.length ? `
        <div>
          <h2 class="recommendations-results-title">Recommended for You (${results.length})</h2>
          <div class="grid">
            ${results.map(item => card(item)).join("")}
          </div>
        </div>
      ` : state.recTriggered ? `
        <div class="empty-state">
          <div class="empty-icon">★</div>
          <h3>No recommendations resolved</h3>
          <p>Try refining your query or trying a different anime title.</p>
        </div>
      ` : ""}
    </div>
  `;

  // Bind events for the recommender page inputs and actions
  const textarea = document.getElementById("recDescInput");
  if (textarea) {
    textarea.addEventListener("input", (e) => {
      state.recommenderQuery = e.target.value;
      const btn = document.getElementById("getDescRecsBtn");
      if (btn) btn.disabled = !state.recommenderQuery.trim();
    });
  }

  const animeInput = document.getElementById("recAnimeInput");
  if (animeInput) {
    animeInput.addEventListener("input", (e) => {
      state.recommenderAnimeTitle = e.target.value;
      const btn = document.getElementById("getAnimeRecsBtn");
      if (btn) btn.disabled = !state.recommenderAnimeTitle.trim();
      setupAutocomplete(animeInput, document.getElementById("recAnimeSuggestions"), true);
    });
    animeInput.addEventListener("focus", () => {
      setupAutocomplete(animeInput, document.getElementById("recAnimeSuggestions"), true);
    });
  }

  const descBtn = document.getElementById("getDescRecsBtn");
  if (descBtn) {
    descBtn.addEventListener("click", async () => {
      state.recLoading = true;
      state.recTriggered = true;
      renderRecommendations();
      try {
        let data = { results: [] };
        try {
          const api = store.getState().api || {};
          const baseUrl = api.baseUrl || "http://127.0.0.1:5000";
          const res = await fetch(`${baseUrl}/api/recommendations/description?description=${encodeURIComponent(state.recommenderQuery)}`);
          if (res.ok) {
            data = await res.json();
          } else {
            throw new Error("Backend description recommender failed");
          }
        } catch (err) {
          console.warn("Backend recommendations by description failed, running direct browser fallback:", err);
          const res = await fetch(`https://api.jikan.moe/v4/top/anime?limit=25`);
          if (res.ok) {
            const payload = await res.json();
            const topList = (payload.data || []).map(item => mapJikanToNompyr(item, "Completed"));
            const queryWords = state.recommenderQuery.toLowerCase().split(/\s+/).filter(w => w.length > 3);
            const scored = topList.map(anime => {
              let score = 0;
              const text = `${anime.title} ${anime.genres.join(" ")} ${anime.description}`.toLowerCase();
              queryWords.forEach(word => {
                if (text.includes(word)) score += 1;
              });
              return { anime, score };
            });
            scored.sort((a, b) => b.score - a.score);
            data = {
              results: scored.filter(s => s.score > 0).map(s => s.anime).slice(0, 12)
            };
            if (data.results.length === 0) {
              data.results = topList.slice(0, 12);
            }
          }
        }
        state.recommenderResults = (data.results || []).map(item => normalizeAnime(item));
      } catch (err) {
        showToast("Error retrieving recommendations.");
      } finally {
        state.recLoading = false;
        renderRecommendations();
      }
    });
  }

  const animeBtn = document.getElementById("getAnimeRecsBtn");
  if (animeBtn) {
    animeBtn.addEventListener("click", async () => {
      state.recLoading = true;
      state.recTriggered = true;
      renderRecommendations();
      try {
        let data = { results: [] };
        try {
          const api = store.getState().api || {};
          const baseUrl = api.baseUrl || "http://127.0.0.1:5000";
          const res = await fetch(`${baseUrl}/api/recommendations/anime?title=${encodeURIComponent(state.recommenderAnimeTitle)}`);
          if (res.ok) {
            data = await res.json();
          } else {
            throw new Error("Backend anime recommendations failed");
          }
        } catch (err) {
          console.warn("Backend recommendations by anime failed, running direct browser fallback:", err);
          const searchRes = await fetch(`https://api.jikan.moe/v4/anime?q=${encodeURIComponent(state.recommenderAnimeTitle)}&limit=1`);
          if (searchRes.ok) {
            const searchData = await searchRes.json();
            if (searchData.data && searchData.data.length > 0) {
              const malId = searchData.data[0].mal_id;
              const recsRes = await fetch(`https://api.jikan.moe/v4/anime/${malId}/recommendations`);
              if (recsRes.ok) {
                const recsData = await recsRes.json();
                const list = recsData.data || [];
                data = {
                  results: list.slice(0, 12).map(rec => {
                    const entry = rec.entry;
                    return {
                      id: `jikan:${entry.mal_id}`,
                      title: entry.title,
                      poster: entry.images?.jpg?.large_image_url || entry.images?.jpg?.image_url || "",
                      type: "TV",
                      score: "N/A",
                      episodes: 12,
                      latestEpisode: 1,
                      language: ["Sub", "Dub"]
                    };
                  })
                };
              }
            }
          }
        }
        state.recommenderResults = (data.results || []).map(item => normalizeAnime(item));
      } catch (err) {
        showToast("Error retrieving recommendations.");
      } finally {
        state.recLoading = false;
        renderRecommendations();
      }
    });
  }
};

const sInput = document.querySelector("#searchInput");
if (sInput) {
  sInput.addEventListener("input", (event) => {
    setupAutocomplete(event.target, document.querySelector("#searchSuggestions"));
  });
  sInput.addEventListener("focus", (event) => {
    setupAutocomplete(event.target, document.querySelector("#searchSuggestions"));
  });
}

render();
