import { animeCatalog, days } from "../data/anime.js?v=11";
import { store } from "./store.js?v=10";

const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
const unwrap = (payload) => payload?.data || payload?.result || payload;
const fallbackPoster = "https://images.unsplash.com/photo-1541562232579-512a21360020?auto=format&fit=crop&w=720&q=80";
const fallbackBanner = "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1600&q=80";

/* ===================================================================
   DEDUPLICATION ENGINE
   =================================================================== */
const normalizeTitle = (title = "") =>
  String(title)
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "")
    .replace(/(season\d+|part\d+|s\d+|cour\d+)$/g, "");

const deduplicateAnime = (list = []) => {
  const seen = new Map();
  for (const anime of list) {
    const key = normalizeTitle(anime.title);
    if (!key) continue;
    const existing = seen.get(key);
    if (!existing) {
      seen.set(key, anime);
    } else {
      // Keep the entry with richer metadata
      const existingScore = (existing.description?.length || 0) + (existing.episodes || 0) +
        (existing.poster && !existing.poster.includes("unsplash") ? 50 : 0);
      const newScore = (anime.description?.length || 0) + (anime.episodes || 0) +
        (anime.poster && !anime.poster.includes("unsplash") ? 50 : 0);
      if (newScore > existingScore) {
        seen.set(key, anime);
      }
    }
  }
  return [...seen.values()];
};

/* ===================================================================
   KNOWN SOURCES DIRECTORY (90 sources from EverythingMoe + extras)
   =================================================================== */
export const KNOWN_SOURCES = [
  { name: "Anikoto", tags: [], status: "connected" },
  { name: "Animepahe", tags: [], status: "directory" },
  { name: "MKissa", tags: [], status: "connected" },
  { name: "Re:Anime", tags: [], status: "directory" },
  { name: "Miruro", tags: ["MULT"], status: "connected" },
  { name: "AniDB", tags: [], status: "connected" },
  { name: "Animetsu", tags: ["MULT"], status: "directory" },
  { name: "AniZone", tags: [], status: "directory" },
  { name: "AniNeko", tags: [], status: "connected" },
  { name: "Senshi", tags: [], status: "connected" },
  { name: "AnimeVerse", tags: [], status: "directory" },
  { name: "AnimeStream", tags: [], status: "directory" },
  { name: "KickAssAnime", tags: [], status: "directory" },
  { name: "AnimeOnsen", tags: [], status: "directory" },
  { name: "Anime Nexus", tags: [], status: "connected" },
  { name: "Anibd.app", tags: [], status: "directory" },
  { name: "AniSnatch", tags: ["MULT"], status: "directory" },
  { name: "AnimeX", tags: ["MULT"], status: "directory" },
  { name: "aniwaves.ru", tags: [], status: "directory" },
  { name: "Anify", tags: [], status: "directory" },
  { name: "Anikuro", tags: ["MULT"], status: "directory" },
  { name: "AnimeParadise", tags: [], status: "directory" },
  { name: "2Dhive", tags: [], status: "directory" },
  { name: "AniHQ", tags: [], status: "directory" },
  { name: "AnimeHeaven", tags: [], status: "directory" },
  { name: "Anikage", tags: ["MULT"], status: "directory" },
  { name: "Anidap", tags: ["MULT"], status: "directory" },
  { name: "Just4Anime", tags: ["MULT"], status: "directory" },
  { name: "Lunar Animes", tags: ["MULT"], status: "directory" },
  { name: "ANIMEGG", tags: [], status: "directory" },
  { name: "AnimeHub", tags: [], status: "directory" },
  { name: "Animotvslash", tags: [], status: "directory" },
  { name: "HIDIVE", tags: [], status: "directory" },
  { name: "AniWorld", tags: [], status: "directory" },
  { name: "FireAnime", tags: [], status: "directory" },
  { name: "Anime-Loads", tags: [], status: "directory" },
  { name: "WCO", tags: [], status: "directory" },
  { name: "Kisskh", tags: [], status: "directory" },
  { name: "Otaku-Streamers", tags: ["LOGIN"], status: "directory" },
  { name: "AnimeNoSub", tags: [], status: "directory" },
  { name: "KimoiTV", tags: [], status: "directory" },
  { name: "Animo", tags: [], status: "directory" },
  { name: "1Anime", tags: ["MULT"], status: "directory" },
  { name: "Shiroko", tags: ["MULT"], status: "directory" },
  { name: "AV1 EnCodes", tags: [], status: "directory" },
  { name: "bettermelon", tags: [], status: "directory" },
  { name: "Zenkai", tags: [], status: "directory" },
  { name: "JustAnime", tags: ["MULT"], status: "directory" },
  { name: "Luna", tags: ["MULT"], status: "directory" },
  { name: "Fanime", tags: ["MULT"], status: "directory" },
  { name: "AnimeDex", tags: ["MULT"], status: "directory" },
  { name: "Animeyubi", tags: ["MULT"], status: "directory" },
  { name: "AniLight", tags: ["MULT"], status: "directory" },
  { name: "YumeZone", tags: ["MULT"], status: "directory" },
  { name: "Itachi", tags: ["MULT"], status: "directory" },
  { name: "AnimeKizz", tags: ["MULT"], status: "directory" },
  { name: "Kyren", tags: ["MULT"], status: "directory" },
  { name: "Animelok", tags: ["MULT"], status: "directory" },
  { name: "Anistream", tags: ["MULT"], status: "directory" },
  { name: "Anime Libre", tags: [], status: "directory" },
  { name: "gogoanime.by", tags: [], status: "directory" },
  { name: "AniVibe", tags: [], status: "directory" },
  { name: "Netflix", tags: [], status: "directory" },
  { name: "OceanVeil", tags: [], status: "directory" },
  { name: "RetroCrush", tags: [], status: "directory" },
  { name: "Yomi", tags: ["MULT"], status: "directory" },
  { name: "Anime Silo", tags: ["KOTO"], status: "directory" },
  { name: "Kaori", tags: ["MULT"], status: "directory" },
  { name: "Otakutsu", tags: ["MULT"], status: "directory" },
  { name: "PimpAnime", tags: ["MULT"], status: "directory" },
  { name: "NekoWatch", tags: ["MULT"], status: "directory" },
  { name: "Animegers", tags: ["MULT"], status: "directory" },
  { name: "Kawaii Anime", tags: ["MULT"], status: "directory" },
  { name: "ani.pm", tags: ["MULT"], status: "directory" },
  { name: "StreamX", tags: ["MULT"], status: "directory" },
  { name: "aniwavecomse", tags: ["KOTO"], status: "directory" },
  { name: "AniverseHD", tags: ["MULT"], status: "directory" },
  { name: "RamenFlix", tags: ["MULT"], status: "directory" },
  { name: "Hulu", tags: [], status: "directory" },
  { name: "Zanora", tags: ["KOTO"], status: "directory" },
  { name: "Animeya", tags: ["MULT"], status: "directory" },
  { name: "Enma", tags: ["KOTO"], status: "directory" },
  { name: "Anime-Dunya", tags: [], status: "directory" },
  { name: "AnimeEpisodeSeries", tags: [], status: "directory" },
  { name: "Kayoanimetv", tags: [], status: "directory" },
  { name: "AnimeWorld", tags: [], status: "directory" },
  { name: "AnimeDekho", tags: [], status: "connected" },
  // Meta/Tracking sources
  { name: "Jikan/MAL", tags: ["META"], status: "connected" },
  { name: "Nompyr Demo", tags: ["DEMO"], status: "connected" },
];

const slugFromUrl = (url = "") => {
  if (!url) return "";
  const clean = String(url).trim().replace(/\/$/, "");
  const parts = clean.split("/");
  return parts.at(-1) || "";
};

const cleanUrl = (url = "") =>
  String(url)
    .trim()
    .replace(/^['"]|['"]$/g, "")
    .replace("https://animekai.behttps://animekai.be", "https://animekai.be")
    .replace("http://127.0.0.1:5000http://127.0.0.1:5000", "http://127.0.0.1:5000");

const splitGenres = (value) => {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  return String(value)
    .split(/[,/]/)
    .map((item) => item.trim())
    .filter(Boolean);
};

const getProxiedImageUrl = (imageUrl) => {
  if (!imageUrl) return imageUrl;
  if (imageUrl.includes("hanime-cdn.com") || imageUrl.includes("hanime.tv") || imageUrl.includes("weeb.sh") || imageUrl.includes("htv-services.com") || imageUrl.includes("cdn.anidb.app")) {
    const api = store.getState().api || {};
    const baseUrl = api.baseUrl ?? "";
    return `${baseUrl}/api/proxy-image?url=${encodeURIComponent(imageUrl)}`;
  }
  return imageUrl;
};

export const mapJikanToNompyr = (item, status) => {
  if (!item) return null;
  const mal_id = item.mal_id;
  const title = item.title || "Untitled";
  const poster = item.images?.jpg?.large_image_url || item.images?.jpg?.image_url || fallbackPoster;
  const genres = (item.genres || []).map(g => g.name);
  if (!status) {
    const j_status = (item.status || "").toLowerCase();
    if (j_status.includes("airing")) status = "Ongoing";
    else if (j_status.includes("upcoming")) status = "Upcoming";
    else status = "Completed";
  }
  const episodes = item.episodes || 1;
  return {
    id: `jikan:${mal_id}`,
    sourceAnimeId: String(mal_id),
    title,
    jpTitle: item.title_japanese || title,
    type: item.type || "TV",
    status,
    year: item.year || item.aired?.prop?.from?.year || 2026,
    season: item.season || "Spring",
    rating: item.rating || "PG-13",
    score: item.score || "N/A",
    duration: item.duration || "24m",
    studio: item.studios?.[0]?.name || "Unknown Studio",
    genres,
    language: ["Sub", "Dub"],
    episodes: episodes,
    latestEpisode: status === "Completed" ? episodes : 1,
    updatedAt: new Date().toISOString().slice(0, 10),
    schedule: "TBA",
    color: "#7c3aed",
    accent: "#f97316",
    poster,
    banner: poster,
    description: item.synopsis || "No description is available from the configured data source yet.",
    tags: genres.slice(0, 3),
    sourceHealth: "Healthy"
  };
};

export const normalizeAnime = (anime = {}, fallbackId = "") => ({
  id: anime.id || anime.slug || slugFromUrl(anime.url) || fallbackId || anime.animeId || anime.ani_id || "unknown",
  sourceAnimeId: anime.sourceAnimeId || anime.ani_id || anime.animeId || "",
  title: anime.title || anime.name || "Untitled Anime",
  jpTitle: anime.jpTitle || anime.japaneseTitle || anime.japanese || anime.title || anime.name || "Untitled Anime",
  type: anime.type || "TV",
  status: anime.status || "Unknown",
  year: anime.year || anime.releaseYear || anime.release || anime.detail?.premiered || "TBA",
  season: anime.season || "TBA",
  rating: anime.rating || anime.ageRating || "PG-13",
  score: anime.score || anime.mal_score || anime.ratingScore || anime.vote || "N/A",
  duration: anime.duration || anime.detail?.duration || "24m",
  studio: anime.studio || anime.studios?.[0] || anime.detail?.studios?.[0] || "Unknown Studio",
  genres: splitGenres(anime.genres || anime.genre || anime.detail?.genres),
  language: anime.language || anime.languages || [anime.sub_episodes ? "Sub" : "", anime.dub_episodes ? "Dub" : ""].filter(Boolean),
  episodes: Number(anime.episodes || anime.totalEpisodes || anime.total_episodes || anime.episodeCount || anime.latestEpisode || anime.sub_episodes || anime.dub_episodes || 1),
  latestEpisode: Number(anime.latestEpisode || anime.latest || anime.current_episode || anime.episode || anime.episodes || anime.sub_episodes || anime.dub_episodes || 1),
  updatedAt: anime.updatedAt || anime.updated || new Date().toISOString().slice(0, 10),
  schedule: anime.schedule || anime.day || "TBA",
  color: anime.color || "#7c3aed",
  accent: anime.accent || "#ec4899",
  poster: getProxiedImageUrl(cleanUrl(anime.poster || anime.image || anime.cover || anime.thumbnail) || fallbackPoster),
  banner: getProxiedImageUrl(cleanUrl(anime.banner || anime.backdrop || anime.poster || anime.image) || fallbackBanner),
  description: anime.description || anime.synopsis || "No description is available from the configured data source yet.",
  tags: anime.tags || [],
  sourceHealth: anime.sourceHealth || "Remote",
  trailer_url: anime.trailer_url || anime.trailerUrl || ""
});

class RemoteApiSource {
  constructor() {
    this.name = "Configured Data API";
    this.priority = 0;
    this.animeIds = new Map();
    this.animeCache = new Map();
  }

  config() {
    let api = store.getState().api || {};
    // Auto-configure to same origin if not explicitly set so the prototype works out of the box
    if (!api.enabled || api.baseUrl == null) {
      api = { ...api, enabled: true, baseUrl: "" };
    }
    if (api.provider === "generic" && !api.key) {
      // Don't enforce key for generic if we default
    }
    return api;
  }

  async request(path, params = {}) {
    const api = this.config();
    const url = new URL(`${api.baseUrl}${path}`, window.location.origin);
    if (api.provider && api.provider !== "generic") {
      params.source = api.provider;
    }
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
    });
    const headers = { Accept: "application/json" };
    if (api.key) {
      headers["x-api-key"] = api.key;
      headers.Authorization = `Bearer ${api.key}`;
    }
    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`Remote API returned ${response.status}`);
    }
    const payload = unwrap(await response.json());
    if (payload && payload.error) {
      throw new Error(payload.error);
    }
    return payload;
  }

  normalizeList(payload) {
    const list = Array.isArray(payload) ? payload : payload?.items || payload?.results || payload?.anime || [];
    if (list.some((item) => item?.error)) {
      throw new Error(list.find((item) => item?.error).error);
    }
    return list
      .filter((item) => {
        // Drop purely metadata or upcoming items with absolutely no uploaded episodes
        const sub = item.sub_episodes;
        const dub = item.dub_episodes;
        const eps = item.episodes || item.total_episodes || item.current_episode;
        
        // If the backend explicitly told us there are no episodes (0 or empty string), filter it out
        if (
          (sub === 0 || sub === "0" || sub === "") &&
          (dub === 0 || dub === "0" || dub === "") &&
          (eps === 0 || eps === "0" || eps === "" || eps === undefined)
        ) {
          return false; // No playable sources yet
        }
        return true;
      })
      .map((item) => normalizeAnime(item));
  }

  async home() {
    const payload = await this.request("/api/home");
    const topTrending = payload.top_trending || {};
    const latest = this.normalizeList(payload.latest || payload.latest_updates || payload.latestEpisodes || payload.recent || []);
    const trending = this.normalizeList(payload.trending || topTrending.NOW || topTrending.DAY || payload.popular || []);
    const spotlight = this.normalizeList(payload.spotlight || payload.banner || payload.banners || trending);
    const primary = spotlight.length ? spotlight : trending.length ? trending : latest;
    if (!primary.length) {
      throw new Error("Remote API returned no home content");
    }
    return {
      spotlight: primary,
      trending,
      latest: latest.length ? latest : trending,
      popular: this.normalizeList(payload.popular || topTrending.WEEK || trending),
      movies: this.normalizeList(payload.movies || []),
      upcoming: this.normalizeList(payload.upcoming || topTrending.MONTH || [])
    };
  }

  async search(params = {}) {
    const query = params.query || "";
    const page = params.page || 1;
    const payload = await this.request("/api/search", {
      keyword: query,
      page,
      source: params.source || "",
      genre: params.genre || "",
      type: params.type || "",
      status: params.status || "",
      year: params.year || "",
      rating: params.rating || "",
      score: params.score || "",
      season: params.season || "",
      language: params.language || "",
      start_year: params.startYear || "",
      start_month: params.startMonth || "",
      start_day: params.startDay || "",
      end_year: params.endYear || "",
      end_month: params.endMonth || "",
      end_day: params.endDay || "",
      sort: params.sort || "",
      genres: (params.genres || []).join(",")
    });
    const results = this.normalizeList(payload);
    return {
      results,
      total: payload?.total || results.length,
      page: payload?.page || page
    };
  }

  async anime(slug) {
    const payload = await this.request(`/api/anime/${encodeURIComponent(slug)}`);
    if (!payload || (!payload.title && !payload.name)) {
      throw new Error("404: Anime not found or invalid data returned from API");
    }
    const anime = normalizeAnime(payload, slug);
    anime.id = slug;
    if (anime.sourceAnimeId) this.animeIds.set(slug, anime.sourceAnimeId);
    this.animeCache.set(slug, anime);
    return anime;
  }

  async episodes(slug) {
    const payload = await this.request(`/api/episodes/${encodeURIComponent(slug)}`);
    let list = Array.isArray(payload) ? payload : payload?.episodes || payload?.items;
    if (list && typeof list === "object" && !Array.isArray(list)) {
      list = Object.values(list);
    }
    list = list || [];
    
    // If no episodes are returned, throw 404 to trigger the graceful fallback UI
    if (list.length === 0) {
      throw new Error("404: No playable episodes returned from API");
    }
    
    // If the episodes are purely metadata (no streaming IDs provided), also throw 404
    // to prevent routing the user to the Demo Player.
    if (!list.some(ep => ep.id || ep.token || ep.ep_token)) {
      throw new Error("404: No streaming sources available for this anime yet");
    }
    
    return list.map((episode, index) => ({
      id: episode.id || episode.token || episode.ep_token || `${slug}-ep-${episode.number || index + 1}`,
      animeId: slug,
      number: episode.number || episode.episode || index + 1,
      title: episode.title || `Episode ${episode.number || index + 1}`,
      released: episode.released !== false,
      duration: episode.duration || "24m"
    }));
  }

  async servers(episodeId) {
    if (episodeId.includes("-ep-")) {
      return [
        { id: `${episodeId}-metadata`, label: "Metadata Only", mode: "Info", quality: ["N/A"] }
      ];
    }
    const payload = await this.request(`/api/servers/${encodeURIComponent(episodeId)}`);
    const grouped = payload?.servers && !Array.isArray(payload.servers) ? Object.entries(payload.servers).flatMap(([mode, servers]) => servers.map((server) => ({ ...server, mode }))) : null;
    const list = grouped || (Array.isArray(payload) ? payload : payload?.servers || payload?.items || []);
    return list.map((server, index) => ({
      id: server.id || server.link_id || server.token || `${episodeId}-server-${index + 1}`,
      label: server.label || server.name || `Server ${index + 1}`,
      mode: server.mode || server.type || "Sub",
      quality: server.quality || server.qualities || ["720p"]
    }));
  }

  async stream(serverId) {
    if (serverId.includes("-metadata") || serverId.includes("-primary")) {
      return {
        serverId,
        hls: "",
        demoOnly: true,
        message: "Metadata source connected. Streaming is disabled in this prototype; connect licensed playback for video.",
        intro: [0, 0],
        outro: [0, 0]
      };
    }
    try {
      const payload = await this.request(`/api/source/${encodeURIComponent(serverId)}`);
      const hlsSource = payload?.sources?.find((s) => s.type === "hls") || payload?.sources?.[0];
      return {
        serverId,
        hls: hlsSource?.file || "",
        type: hlsSource?.type || "hls",
        embed_url: payload?.embed_url || "",
        intro: payload?.skip?.intro || [0, 0],
        outro: payload?.skip?.outro || [0, 0],
        tracks: payload?.tracks || [],
        download: payload?.download || "",
        external_url: payload?.external_url || "",
        provider: payload?.provider || "",
        message: payload?.message || ((hlsSource?.file || payload?.embed_url) ? "" : "No source resolved.")
      };
    } catch (error) {
      return {
        serverId,
        hls: "",
        intro: [0, 0],
        outro: [0, 0],
        message: `Error resolving stream: ${error.message}`
      };
    }
  }

  async download(serverId, quality) {
    if (serverId.includes("-metadata") || serverId.includes("-primary")) {
      return {
        serverId,
        quality,
        demoOnly: true,
        message: "Download resolution is disabled in this prototype; connect licensed downloads in your Worker."
      };
    }
    try {
      const payload = await this.request(`/api/source/${encodeURIComponent(serverId)}`);
      if (payload?.download) {
        return {
          serverId,
          quality,
          url: payload.download,
          message: "Opening download link..."
        };
      }
      return {
        serverId,
        quality,
        demoOnly: true,
        message: "No download link resolved from the source."
      };
    } catch (error) {
      return {
        serverId,
        quality,
        demoOnly: true,
        message: `Error resolving download: ${error.message}`
      };
    }
  }

  async schedule() {
    const payload = await this.request("/api/schedule");
    return Array.isArray(payload) ? payload : payload?.schedule || [];
  }

  async recommendations(title) {
    try {
      const payload = await this.request("/api/recommendations/anime", { title });
      return Array.isArray(payload) ? payload.map(item => normalizeAnime(item)) : (payload?.results || []).map(item => normalizeAnime(item));
    } catch {
      return [];
    }
  }

  async jikanLists() {
    try {
      return await this.request("/api/jikan-lists");
    } catch (error) {
      console.warn("Remote API jikanLists failed, trying direct fetch:", error);
      return this.directJikanFetch();
    }
  }

  async directJikanFetch() {
    try {
      const rNow = await fetch("https://api.jikan.moe/v4/seasons/now?limit=25");
      await wait(400);
      const rUpcoming = await fetch("https://api.jikan.moe/v4/seasons/upcoming?limit=25");
      await wait(400);
      const rTop = await fetch("https://api.jikan.moe/v4/top/anime?limit=25");
      
      const nowData = await rNow.json();
      const upcomingData = await rUpcoming.json();
      const topData = await rTop.json();
      
      return {
        success: true,
        newReleases: (nowData.data || []).map(item => mapJikanToNompyr(item, "Ongoing")),
        upcoming: (upcomingData.data || []).map(item => mapJikanToNompyr(item, "Upcoming")),
        completed: (topData.data || []).map(item => mapJikanToNompyr(item, "Completed"))
      };
    } catch (error) {
      console.error("Direct Jikan fetch failed:", error);
      return this.staticListsFallback();
    }
  }

  staticListsFallback() {
    const generateSimulated = (prefix, status, count = 20) => {
      return Array.from({ length: count }, (_, i) => ({
        id: `simulated:${prefix}-${i + 1}`,
        title: `${prefix} Anime Title ${i + 1}`,
        jpTitle: `Nihongo Title ${i + 1}`,
        type: i % 3 === 0 ? "Movie" : "TV",
        status,
        year: 2025 - (i % 5),
        season: ["Spring", "Summer", "Fall", "Winter"][i % 4],
        rating: "PG-13",
        score: (8.9 - i * 0.1).toFixed(1),
        duration: "24m",
        studio: "Studio Sunrise",
        genres: ["Action", "Sci-Fi"],
        language: ["Sub", "Dub"],
        episodes: status === "Completed" ? 12 : 1,
        latestEpisode: status === "Completed" ? 12 : 1,
        updatedAt: new Date().toISOString().slice(0, 10),
        schedule: "TBA",
        color: "#7c3aed",
        accent: "#f97316",
        poster: fallbackPoster,
        banner: fallbackBanner,
        description: "This is a simulated placeholder anime description. Real data will load once connection to Jikan API is established.",
        tags: ["Action", "Sci-Fi"],
        sourceHealth: "Healthy"
      }));
    };
    return {
      success: true,
      newReleases: generateSimulated("New Release", "Ongoing", 20),
      upcoming: generateSimulated("Upcoming", "Upcoming", 20),
      completed: generateSimulated("Completed", "Completed", 20)
    };
  }
}

class DemoSource {
  constructor() {
    this.name = "Nompyr Demo Source";
    this.priority = 1;
  }

  async home() {
    await wait();
    return {
      spotlight: [
        {
          id: "https://www.animenewsnetwork.com/news/2026-06-23/paranormasight-spinoff-manga-listed-to-end-with-2nd-volume/.238817",
          title: "PARANORMASIGHT Spinoff Manga Listed to End With 2nd Volume",
          description: "The 2nd compiled volume of the spinoff manga will ship on August 6, marking the conclusion of the series.",
          poster: "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1600&q=80",
          banner: "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1600&q=80",
          year: "2026",
          rating: "Manga",
          status: "Completed",
          type: "Article",
          genres: ["Manga"],
          score: "News",
          isNews: true
        },
        {
          id: "https://www.animenewsnetwork.com/news/2026-06-23/abrams-comicarts-kana-licenses-qtonagi-hotel-astrology-book/.238821",
          title: "Abrams ComicArts' Kana Licenses Qtonagi's Hotel Astrology Book",
          description: "The new astrology and horoscope book is scheduled to ship in fall 2027 under the Kana imprint.",
          poster: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
          banner: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
          year: "2027",
          rating: "Book",
          status: "Completed",
          type: "Article",
          genres: ["Book"],
          score: "News",
          isNews: true
        },
        {
          id: "https://www.animenewsnetwork.com/news/2026-06-23/uta-no-prince-sama-dolce-vita-uta-no-prince-sama-shining-live-games-announce-release-dates/.238850",
          title: "Uta no Prince-sama Dolce Vita, Uta no Prince-sama Shining Live Games Release Dates",
          description: "Uta no Prince-sama Shining Live launches on December 17, and Uta no Prince-sama Dolce Vita launches in 2027.",
          poster: "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1600&q=80",
          banner: "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1600&q=80",
          year: "2026",
          rating: "Games",
          status: "Completed",
          type: "Article",
          genres: ["Games"],
          score: "News",
          isNews: true
        },
        {
          id: "https://www.animenewsnetwork.com/news/2026-06-23/sonic-racing-crossworlds-game-adds-classic-sonic-crazy-taxi-axel-samba-de-amigo-amigo/.238852",
          title: "Sonic Racing CrossWorlds Game Adds Classic Sonic, Axel, Amigo",
          description: "The game adds Classic Sonic on Tuesday, Crazy Taxi's Axel in August, and Samba de Amigo's Amigo in September.",
          poster: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1600&q=80",
          banner: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1600&q=80",
          year: "2026",
          rating: "Games",
          status: "Completed",
          type: "Article",
          genres: ["Games"],
          score: "News",
          isNews: true
        },
        {
          id: "https://www.animenewsnetwork.com/news/2026-06-23/cake-wep-partner-to-distribute-voltron-franchise/.238813",
          title: "CAKE, WEP Partner to Distribute Voltron Franchise",
          description: "The distributed catalog includes Voltron: Golion, Voltron: Dairugger XV, and other classic titles.",
          poster: "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=1600&q=80",
          banner: "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=1600&q=80",
          year: "2026",
          rating: "Anime",
          status: "Completed",
          type: "Article",
          genres: ["Anime"],
          score: "News",
          isNews: true
        }
      ],
      trending: [...animeCatalog].sort((a, b) => b.score - a.score),
      latest: [...animeCatalog].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)),
      popular: animeCatalog.filter((anime) => anime.score >= 8.4),
      movies: animeCatalog.filter((anime) => anime.type === "Movie"),
      upcoming: animeCatalog.filter((anime) => anime.status === "Upcoming")
    };
  }

  async recommend(animeId) {
    await wait(100);
    const target = animeCatalog.find((a) => a.id === animeId);
    if (!target) return animeCatalog.slice(0, 12);
    
    // "RelatedAnime" inspired recommendation algorithm
    return animeCatalog
      .filter((a) => a.id !== animeId)
      .map(a => {
        let score = 0;
        // Shared studio is a strong signal
        if (a.studio && target.studio && a.studio === target.studio) score += 3;
        
        // Shared genres (each adds 1 point)
        if (a.genres && target.genres) {
          const common = a.genres.filter(g => target.genres.includes(g));
          score += common.length;
        }
        
        // Match franchise (if title starts similarly)
        if (a.title && target.title) {
            const t1 = a.title.split(" ")[0].toLowerCase();
            const t2 = target.title.split(" ")[0].toLowerCase();
            if (t1 === t2 && t1.length > 3) score += 5;
        }
        
        // Match format (e.g. TV vs Movie)
        if (a.format && target.format && a.format === target.format) score += 1;
        
        return { anime: a, score };
      })
      .filter(a => a.score > 0)
      .sort((a, b) => b.score - a.score || Math.random() - 0.5)
      .map(a => a.anime)
      .slice(0, 12);
  }

  async search(params = {}) {
    await wait(80);
    const query = (params.query || "").toLowerCase();
    const allResults = animeCatalog.filter((anime) => {
      const text = [anime.title, anime.jpTitle, anime.studio, anime.type, anime.status, ...anime.genres, ...anime.tags]
        .join(" ")
        .toLowerCase();
      const matchesQuery = !query || text.includes(query);
      const matchesGenre = !params.genre || anime.genres.includes(params.genre);
      const matchesType = !params.type || anime.type === params.type;
      const matchesStatus = !params.status || anime.status === params.status;
      const matchesYear = !params.year || String(anime.year) === String(params.year);
      return matchesQuery && matchesGenre && matchesType && matchesStatus && matchesYear;
    });

    const page = params.page || 1;
    const perPage = 30;
    const start = (page - 1) * perPage;
    const paginated = allResults.slice(start, start + perPage);

    return {
      results: paginated.map((item) => normalizeAnime(item)),
      total: allResults.length,
      page
    };
  }

  async anime(slug) {
    await wait(80);
    if (slug.startsWith("jikan:")) {
      try {
        const malId = slug.split("jikan:")[1];
        const res = await fetch(`https://api.jikan.moe/v4/anime/${malId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.data) {
            return mapJikanToNompyr(data.data);
          }
        }
      } catch (err) {
        console.warn("Direct Jikan details fetch failed:", err);
      }
    }
    const anime = animeCatalog.find((item) => item.id === slug || item.slug === slug);
    if (anime) return anime;

    // Dynamically generate a simulated fallback anime details object
    const provider = slug.includes(":") ? slug.split(":")[0] : "demo";
    const cleanSlug = slug.includes(":") ? slug.split(":")[1] : slug;
    const title = cleanSlug
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

    return {
      id: slug,
      sourceAnimeId: cleanSlug,
      title: title,
      jpTitle: title,
      type: "TV",
      status: "Ongoing",
      year: new Date().getFullYear(),
      season: "Spring",
      rating: "PG-13",
      score: "8.0",
      duration: "24m",
      studio: "Nompyr Studio",
      genres: ["Action", "Adventure"],
      language: ["Sub", "Dub"],
      episodes: 12,
      latestEpisode: 12,
      updatedAt: new Date().toISOString().slice(0, 10),
      schedule: "TBA",
      color: "#7c3aed",
      accent: "#f97316",
      poster: fallbackPoster,
      banner: fallbackBanner,
      description: `This is a dynamically simulated detail view for ${title}. The remote API did not find this show or is offline, so Nompyr has loaded it in demo mode.`,
      tags: ["Action", "Adventure"],
      sourceHealth: `Demo (${provider})`
    };
  }

  async episodes(slug) {
    if (slug.startsWith("jikan:")) {
      const malId = slug.split("jikan:")[1];
      try {
        const res = await fetch(`https://api.jikan.moe/v4/anime/${malId}/episodes`);
        const payload = await res.json();
        const list = payload.data || [];
        if (list.length > 0) {
          return list.map((episode, index) => ({
            id: `${slug}-ep-${episode.mal_id || episode.number || index + 1}`,
            animeId: slug,
            number: episode.mal_id || episode.number || index + 1,
            title: episode.title || `Episode ${episode.number || index + 1}`,
            released: true,
            duration: "24m"
          })).reverse();
        }
      } catch (err) {
        console.warn("Direct Jikan episodes fetch failed:", err);
      }
    }
    const anime = await this.anime(slug);
    const total = anime.episodes || 1;
    return Array.from({ length: total }, (_, index) => {
      const number = index + 1;
      return {
        id: `${slug}-ep-${number}`,
        animeId: slug,
        number,
        title: anime.type === "Movie" ? "Full Movie" : `Episode ${number}`,
        released: number <= anime.latestEpisode,
        duration: anime.duration
      };
    }).reverse();
  }

  async jikanLists() {
    return this.directJikanFetch();
  }

  async directJikanFetch() {
    try {
      const rNow = await fetch("https://api.jikan.moe/v4/seasons/now?limit=25");
      await wait(400);
      const rUpcoming = await fetch("https://api.jikan.moe/v4/seasons/upcoming?limit=25");
      await wait(400);
      const rTop = await fetch("https://api.jikan.moe/v4/top/anime?limit=25");
      
      const nowData = await rNow.json();
      const upcomingData = await rUpcoming.json();
      const topData = await rTop.json();
      
      return {
        success: true,
        newReleases: (nowData.data || []).map(item => mapJikanToNompyr(item, "Ongoing")),
        upcoming: (upcomingData.data || []).map(item => mapJikanToNompyr(item, "Upcoming")),
        completed: (topData.data || []).map(item => mapJikanToNompyr(item, "Completed"))
      };
    } catch (error) {
      console.error("Direct Jikan fetch failed in DemoSource:", error);
      return this.staticListsFallback();
    }
  }

  async recommendations(title) {
    try {
      const searchRes = await fetch(`https://api.jikan.moe/v4/anime?q=${encodeURIComponent(title)}&limit=1`);
      const searchData = await searchRes.json();
      const malId = searchData?.data?.[0]?.mal_id;
      if (!malId) return [];

      const recsRes = await fetch(`https://api.jikan.moe/v4/anime/${malId}/recommendations`);
      const recsData = await recsRes.json();
      return (recsData?.data || []).map(r => mapJikanToNompyr(r.entry)).filter(Boolean);
    } catch (e) {
      console.warn("Direct Jikan recommendations failed in DemoSource:", e);
      return [];
    }
  }

  staticListsFallback() {
    const generateSimulated = (prefix, status, count = 20) => {
      return Array.from({ length: count }, (_, i) => ({
        id: `simulated:${prefix}-${i + 1}`,
        title: `${prefix} Anime Title ${i + 1}`,
        jpTitle: `Nihongo Title ${i + 1}`,
        type: i % 3 === 0 ? "Movie" : "TV",
        status,
        year: 2025 - (i % 5),
        season: ["Spring", "Summer", "Fall", "Winter"][i % 4],
        rating: "PG-13",
        score: (8.9 - i * 0.1).toFixed(1),
        duration: "24m",
        studio: "Studio Sunrise",
        genres: ["Action", "Sci-Fi"],
        language: ["Sub", "Dub"],
        episodes: status === "Completed" ? 12 : 1,
        latestEpisode: status === "Completed" ? 12 : 1,
        updatedAt: new Date().toISOString().slice(0, 10),
        schedule: "TBA",
        color: "#7c3aed",
        accent: "#f97316",
        poster: fallbackPoster,
        banner: fallbackBanner,
        description: "This is a simulated placeholder anime description. Real data will load once connection to Jikan API is established.",
        tags: ["Action", "Sci-Fi"],
        sourceHealth: "Healthy"
      }));
    };
    return {
      success: true,
      newReleases: generateSimulated("New Release", "Ongoing", 20),
      upcoming: generateSimulated("Upcoming", "Upcoming", 20),
      completed: generateSimulated("Completed", "Completed", 20)
    };
  }

  async servers(episodeId) {
    await wait(60);
    return [
      { id: `${episodeId}-sub-primary`, label: "Nompyr Sub", mode: "Sub", quality: ["360p", "480p", "720p", "1080p"] },
      { id: `${episodeId}-dub-primary`, label: "Nompyr Dub", mode: "Dub", quality: ["480p", "720p"] }
    ];
  }

  async stream(serverId) {
    await wait(70);
    return {
      serverId,
      hls: "",
      demoOnly: true,
      message: "Demo mode: connect a licensed source adapter to enable playback.",
      intro: [75, 165],
      outro: [1280, 1360]
    };
  }

  async download(serverId, quality) {
    await wait(70);
    return {
      serverId,
      quality,
      demoOnly: true,
      message: "Downloads are prepared by source adapters and are disabled in this demo."
    };
  }

  async schedule() {
    await wait(80);
    return days.map((day) => ({
      day,
      releases: animeCatalog.filter((anime) => anime.schedule === day)
    }));
  }
}

class ConsumetSource {
  constructor() {
    this.name = "Consumet Fallback API";
    this.priority = 50;
    this.baseUrl = "https://api.consumet.org/anime/gogoanime";
  }

  async searchAnime(slug) {
    let query = slug;
    if (slug.includes(":")) query = slug.split(":").slice(1).join(":");
    query = query.replace(/-/g, " ");
    const res = await fetch(`${this.baseUrl}/${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      return data.results[0].id;
    }
    throw new Error("Anime not found on Consumet");
  }

  async home() { throw new Error("Not implemented"); }
  async search() { throw new Error("Not implemented"); }
  async anime() { throw new Error("Not implemented"); }

  async episodes(slug) {
    const consumetId = await this.searchAnime(slug);
    const res = await fetch(`${this.baseUrl}/info/${consumetId}`);
    const data = await res.json();
    if (!data.episodes || data.episodes.length === 0) {
      throw new Error("No episodes returned from Consumet API");
    }
    return data.episodes.map(ep => ({
      id: ep.id,
      animeId: slug,
      number: ep.number,
      title: `Episode ${ep.number}`,
      released: true,
      duration: "24m"
    })).reverse();
  }

  async servers(episodeId) {
    if (episodeId.includes("-ep-")) throw new Error("Not a Consumet episode ID");
    return [
      { id: episodeId, label: "Consumet (GogoAnime)", mode: "Sub", quality: ["Auto", "1080p", "720p"] }
    ];
  }

  async stream(serverId) {
    if (serverId.includes("-ep-")) throw new Error("Not a Consumet server ID");
    const res = await fetch(`${this.baseUrl}/watch/${serverId}`);
    const data = await res.json();
    const source = data.sources?.find(s => s.quality === "default" || s.quality === "auto") || data.sources?.[0];
    if (source) {
      return {
        serverId,
        hls: source.url,
        demoOnly: false,
        message: "Streaming via Consumet Fallback API"
      };
    }
    throw new Error("Stream not found on Consumet");
  }

  async download() { throw new Error("Not implemented"); }
  async schedule() { throw new Error("Not implemented"); }
}

export class SourceManager {
  constructor(sources = [new RemoteApiSource(), new ConsumetSource()]) {
    this.sources = sources.sort((a, b) => a.priority - b.priority);
  }

  async trySources(method, ...args) {
    const errors = [];
    for (const source of this.sources) {
      try {
        return await source[method](...args);
      } catch (error) {
        errors.push({ source: source.name, message: error.message });
      }
    }
    throw new Error(errors.map((error) => `${error.source}: ${error.message}`).join("; "));
  }

  async home() {
    const data = await this.trySources("home");
    // Deduplicate all lists
    if (data) {
      data.spotlight = deduplicateAnime(data.spotlight || []);
      data.trending = deduplicateAnime(data.trending || []);
      data.latest = deduplicateAnime(data.latest || []);
      data.popular = deduplicateAnime(data.popular || []);
      data.movies = deduplicateAnime(data.movies || []);
      data.upcoming = deduplicateAnime(data.upcoming || []);
    }
    return data;
  }

  async search(params) {
    const data = await this.trySources("search", params);
    if (data && data.results) {
      data.results = deduplicateAnime(data.results);
    }
    return data;
  }

  anime(slug) {
    return this.trySources("anime", slug);
  }

  episodes(slug) {
    return this.trySources("episodes", slug);
  }

  servers(episodeId) {
    return this.trySources("servers", episodeId);
  }

  stream(serverId) {
    return this.trySources("stream", serverId);
  }

  download(serverId, quality) {
    return this.trySources("download", serverId, quality);
  }

  schedule() {
    return this.trySources("schedule");
  }

  jikanLists() {
    return this.trySources("jikanLists");
  }

  recommendations(title) {
    return this.trySources("recommendations", title);
  }

  async historySync(payload) {
    try {
      const api = store.getState().api || {};
      if (!api.enabled || api.baseUrl == null) return;
      
      const url = new URL(`${api.baseUrl}/api/history`, window.location.origin);
      const headers = { "Content-Type": "application/json", Accept: "application/json" };
      if (api.key) {
        headers["x-api-key"] = api.key;
        headers.Authorization = `Bearer ${api.key}`;
      }
      
      await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload)
      });
    } catch (error) {
      console.warn("Failed to sync history to backend:", error);
    }
  }

  async getHistory(sessionId) {
    try {
      const api = store.getState().api || {};
      if (!api.enabled || api.baseUrl == null) return [];
      
      const url = new URL(`${api.baseUrl}/api/history?session_id=${sessionId}`, window.location.origin);
      const headers = { Accept: "application/json" };
      if (api.key) {
        headers["x-api-key"] = api.key;
        headers.Authorization = `Bearer ${api.key}`;
      }
      
      const response = await fetch(url, { headers });
      if (!response.ok) return [];
      const data = await response.json();
      return data.success ? (data.history || []) : [];
    } catch (error) {
      console.warn("Failed to fetch history from backend:", error);
      return [];
    }
  }

  listSources() {
    return KNOWN_SOURCES;
  }

  apiStatus() {
    const api = store.getState().api || {};
    return {
      enabled: Boolean(api.enabled),
      configured: Boolean(api.baseUrl && api.key),
      provider: api.provider || "generic",
      contentReady: Boolean(api.enabled && api.baseUrl),
      baseUrl: api.baseUrl || "Not set"
    };
  }
}

export const sourceManager = new SourceManager();
