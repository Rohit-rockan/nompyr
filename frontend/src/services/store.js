const KEY = "nompyr-state-v1";

const getDynamicDefaultBaseUrl = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  return ""; // Universally use relative paths to leverage Vite/Vercel proxies
};

const initialState = {
  favorites: [],
  history: [],
  progress: {},
  cachedAnime: {},
  api: {
    enabled: true,
    provider: "all",
    baseUrl: getDynamicDefaultBaseUrl(),
    key: ""
  },
  settings: {
    autoplay: true,
    skipIntro: true,
    skipOutro: false,
    theatre: false,
    theme: "dark"
  },
  profile: {
    username: "DaoistGNE3VE",
    joinedDate: "2026-06-14",
    userId: "4325078931",
    location: "Global",
    avatarUrl: "",
    bannerUrl: ""
  },
  friends: [
    { id: "zoro", name: "Roronoa Zoro", avatar: "🟢", status: "online", bio: "Lost, looking for the watch page." },
    { id: "luffy", name: "Monkey D. Luffy", avatar: "🍖", status: "online", bio: "Going to be the Pirate King!" },
    { id: "nami", name: "Nami", avatar: "🍊", status: "offline", bio: "Charging 100,000 berries per review." },
    { id: "goku", name: "Son Goku", avatar: "🔥", status: "online", bio: "Hey, it's me, Goku!" }
  ],
  chatMessages: {
    zoro: [
      { sender: "friend", text: "Hey! Have you seen where the next episode is?", time: "2 hours ago" },
      { sender: "me", text: "It's on the homepage in the continue watching row!", time: "1 hour ago" },
      { sender: "zoro", text: "I still got lost...", time: "10 mins ago" }
    ],
    luffy: [
      { sender: "friend", text: "Hey! Do they serve meat here?", time: "Yesterday" },
      { sender: "me", text: "No, this is a simulated anime catalog site!", time: "Yesterday" }
    ]
  }
};

const read = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY)) || {};
    const api = saved.api?.baseUrl ? { ...initialState.api, ...saved.api } : { ...initialState.api };
    
    // Auto-heal base URL if the loaded configuration is pointing to a local host on a remote domain,
    // or if it is stuck on the old dead Render backend URL from previous cache.
    const isLocalDomain = window.location.origin.includes("127.0.0.1") || window.location.origin.includes("localhost") || window.location.origin.includes("4173");
    if ((!isLocalDomain && api.baseUrl === "http://127.0.0.1:5000") || api.baseUrl === "https://nompyr-backend.onrender.com") {
      api.baseUrl = "";
    }

    if (api.baseUrl === undefined || api.baseUrl === null) {
      api.baseUrl = getDynamicDefaultBaseUrl();
    }

    if (api.provider === "animekai") {
      api.provider = "all";
    }
    return {
      ...initialState,
      ...saved,
      api,
      favorites: saved.favorites || initialState.favorites || [],
      history: saved.history || initialState.history || [],
      progress: saved.progress || initialState.progress || {},
      cachedAnime: saved.cachedAnime || initialState.cachedAnime || {},
      profile: { ...initialState.profile, ...(saved.profile || {}) },
      friends: saved.friends || initialState.friends || [],
      chatMessages: saved.chatMessages || initialState.chatMessages || {},
      settings: { ...initialState.settings, ...(saved.settings || {}) }
    };
  } catch {
    return initialState;
  }
};

const write = (state) => {
  localStorage.setItem(KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent("nompyr:state", { detail: state }));
};

export const store = {
  getState: read,
  cacheAnime(anime) {
    if (!anime || !anime.id) return;
    const state = read();
    if (!state.cachedAnime) state.cachedAnime = {};
    state.cachedAnime[anime.id] = anime;
    write(state);
  },
  toggleFavorite(id) {
    const state = read();
    state.favorites = state.favorites.includes(id) ? state.favorites.filter((item) => item !== id) : [...state.favorites, id];
    write(state);
    return state.favorites.includes(id);
  },
  addHistory(entry) {
    const state = read();
    state.history = [entry, ...state.history.filter((item) => item.episodeId !== entry.episodeId)].slice(0, 40);
    state.progress[entry.episodeId] = entry.progress;
    write(state);
  },
  updateSetting(name, value) {
    const state = read();
    state.settings[name] = value;
    write(state);
  },
  updateApiConfig(config) {
    const state = read();
    state.api = {
      enabled: Boolean(config.enabled),
      provider: config.provider || "generic",
      baseUrl: String(config.baseUrl || "").trim().replace(/\/+$/, ""),
      key: String(config.key || "").trim()
    };
    write(state);
  },
  clearApiConfig() {
    const state = read();
    state.api = { ...initialState.api };
    write(state);
  },
  clearHistory() {
    const state = read();
    state.history = [];
    state.progress = {};
    write(state);
  },
  setSessionId(id) {
    const state = read();
    state.sessionId = id;
    write(state);
  },
  updateProfile(username, location, avatarUrl, bannerUrl) {
    const state = read();
    state.profile = {
      ...state.profile,
      username: username !== undefined ? username : state.profile.username,
      location: location !== undefined ? location : state.profile.location,
      avatarUrl: avatarUrl !== undefined ? avatarUrl : state.profile.avatarUrl,
      bannerUrl: bannerUrl !== undefined ? bannerUrl : state.profile.bannerUrl
    };
    write(state);
    return state.profile;
  },
  addFriend(friend) {
    const state = read();
    if (!state.friends.some(f => f.id === friend.id)) {
      state.friends.push(friend);
    }
    if (!state.chatMessages[friend.id]) {
      state.chatMessages[friend.id] = [];
    }
    write(state);
  },
  removeFriend(friendId) {
    const state = read();
    state.friends = state.friends.filter(f => f.id !== friendId);
    write(state);
  },
  addChatMessage(friendId, message) {
    const state = read();
    if (!state.chatMessages[friendId]) {
      state.chatMessages[friendId] = [];
    }
    state.chatMessages[friendId].push(message);
    write(state);
    return state.chatMessages[friendId];
  },
  exportMALSync() {
    const state = read();
    const exportData = state.history.map(entry => {
      const anime = state.cachedAnime[entry.animeId] || {};
      const malId = anime.sourceAnimeId || anime.id.split(':')[1] || anime.id;
      return {
        malId: malId,
        title: anime.title || entry.title,
        episodesWatched: entry.episode,
        score: anime.score || 0,
        status: 1, // 1 = watching
        updatedAt: entry.date
      };
    });
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nompyr_malsync_export_${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
};
