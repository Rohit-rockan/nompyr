const KEY = "nompyr-state-v1";

const initialState = {
  favorites: [],
  history: [],
  progress: {},
  api: {
    enabled: true,
    provider: "all",
    baseUrl: "http://127.0.0.1:5000",
    key: ""
  },
  settings: {
    autoplay: true,
    skipIntro: true,
    skipOutro: false,
    theatre: false
  }
};

const read = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY)) || {};
    const api = saved.api?.baseUrl ? { ...initialState.api, ...saved.api } : initialState.api;
    if (api.provider === "animekai") {
      api.provider = "all";
    }
    return {
      ...initialState,
      ...saved,
      api,
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
  }
};
