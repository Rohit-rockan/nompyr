import { animeCatalog, days } from "../data/anime.js?v=5";
import { store } from "./store.js?v=5";

const wait = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));
const unwrap = (payload) => payload?.data || payload?.result || payload;
const fallbackPoster = "https://images.unsplash.com/photo-1541562232579-512a21360020?auto=format&fit=crop&w=720&q=80";
const fallbackBanner = "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1600&q=80";

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
  if (imageUrl.includes("hanime-cdn.com") || imageUrl.includes("hanime.tv") || imageUrl.includes("weeb.sh") || imageUrl.includes("htv-services.com")) {
    const api = store.getState().api || {};
    const baseUrl = api.baseUrl || "http://127.0.0.1:5000";
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
    const api = store.getState().api || {};
    if (!api.enabled || !api.baseUrl) {
      throw new Error("Remote API is not configured");
    }
    if (api.provider === "generic" && !api.key) {
      throw new Error("Remote API key is not configured");
    }
    return api;
  }

  async request(path, params = {}) {
    const api = this.config();
    const url = new URL(`${api.baseUrl}${path}`);
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
    return unwrap(await response.json());
  }

  normalizeList(payload) {
    const list = Array.isArray(payload) ? payload : payload?.items || payload?.results || payload?.anime || [];
    if (list.some((item) => item?.error)) {
      throw new Error(list.find((item) => item?.error).error);
    }
    return list.map((item) => normalizeAnime(item));
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
    const anime = normalizeAnime(await this.request(`/api/anime/${encodeURIComponent(slug)}`), slug);
    anime.id = slug;
    if (anime.sourceAnimeId) this.animeIds.set(slug, anime.sourceAnimeId);
    this.animeCache.set(slug, anime);
    return anime;
  }

  async episodes(slug) {
    try {
      const payload = await this.request(`/api/episodes/${encodeURIComponent(slug)}`);
      const list = Array.isArray(payload) ? payload : payload?.episodes || payload?.items || [];
      if (list.length === 0) {
        throw new Error("No episodes returned from API");
      }
      return list.map((episode, index) => ({
        id: episode.id || episode.token || episode.ep_token || `${slug}-ep-${episode.number || index + 1}`,
        animeId: slug,
        number: episode.number || episode.episode || index + 1,
        title: episode.title || `Episode ${episode.number || index + 1}`,
        released: episode.released !== false,
        duration: episode.duration || "24m"
      }));
    } catch (error) {
      console.warn("Failed to fetch episodes from API, falling back to dummy list:", error);
      if (!this.animeCache.has(slug)) {
        try {
          await this.anime(slug);
        } catch (e) {}
      }
      const anime = this.animeCache.get(slug);
      const total = Math.max(1, Number(anime?.episodes || anime?.latestEpisode || 1));
      const start = Math.max(1, total - 99);
      return Array.from({ length: total - start + 1 }, (_, index) => {
        const number = start + index;
        return {
          id: `${slug}-ep-${number}`,
          animeId: slug,
          number,
          title: anime?.type === "Movie" ? "Full Movie" : `Episode ${number}`,
          released: true,
          duration: anime?.duration || "24m"
        };
      }).reverse();
    }
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
        message: hlsSource?.file ? "" : "No HLS source resolved."
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
      spotlight: animeCatalog.slice(0, 4),
      trending: [...animeCatalog].sort((a, b) => b.score - a.score),
      latest: [...animeCatalog].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)),
      popular: animeCatalog.filter((anime) => anime.score >= 8.4),
      movies: animeCatalog.filter((anime) => anime.type === "Movie"),
      upcoming: animeCatalog.filter((anime) => anime.status === "Upcoming")
    };
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

export class SourceManager {
  constructor(sources = [new RemoteApiSource(), new DemoSource()]) {
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

  home() {
    return this.trySources("home");
  }

  search(params) {
    return this.trySources("search", params);
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
