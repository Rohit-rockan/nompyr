# Nompyr

Your Gateway To Infinite Anime.

This workspace contains a functional static prototype for an original anime discovery and watch platform inspired by AnimeKai-style navigation and modern streaming apps. It does not copy AnimeKai source code and does not include third-party stream scraping. Playback and downloads are demo-mode hooks designed for future licensed source adapters.

## Run Locally

```bash
npm run dev
```

Then open:

```text
http://127.0.0.1:4173
```

The app also works as a plain static site from `index.html` when served by any web server.

## Current Pages

- `#/` home with spotlight, trending, latest, top airing, movies, upcoming, and continue watching
- `#/search` instant library search with genre, type, status, and year filters
- `#/anime/:slug` anime details, metadata, episodes, recommendations, and favorite action
- `#/watch/:slug/:episode` demo watch page with server list, progress saving, and download hook
- `#/schedule` weekly release board
- `#/favorites` local favorites
- `#/history` local watch history
- `#/profile` guest settings stored in local storage
- `#/admin` source-health and product metrics dashboard
- Configurable data API base URL and API key from `#/profile`

## Architecture

```text
index.html
src/
  app/main.js                 SPA router and UI rendering
  data/anime.js               Demo catalog data
  services/sourceManager.js   Multi-source interface and demo provider
  services/store.js           Local storage favorites, history, settings
  styles/styles.css           Responsive dark UI system
```

The source manager intentionally mirrors the future provider contract:

```ts
interface AnimeSource {
  home(): Promise<HomePayload>
  search(params: SearchParams): Promise<Anime[]>
  anime(slug: string): Promise<Anime>
  episodes(slug: string): Promise<Episode[]>
  servers(episodeId: string): Promise<Server[]>
  stream(serverId: string): Promise<StreamPayload>
  download(serverId: string, quality: string): Promise<DownloadPayload>
}
```

## Data API Key

Open `#/profile`, add your API base URL and key, then enable "Use configured API for anime data". The AnimeKAI API zip can be selected with the "Use AnimeKAI Local" preset, which points the site to `http://127.0.0.1:5000` and does not require a key.

For generic APIs, the app sends the key as both `x-api-key` and `Authorization: Bearer <key>`.

For this static prototype, the key is stored in browser localStorage. In production, keep provider keys inside a Cloudflare Worker and let the frontend call your own Worker API instead of exposing secrets to the browser.

## AnimeKAI Zip Content

The provided AnimeKAI API zip was tested as a local metadata provider. The local extracted copy used for this prototype lives at:

```text
E:\nompyr\.tmp_api_commit\AnimeKAI-API-387dcdb7664499b405c804520e93d68c653b4487\app.py
```

Run it with:

```bash
python E:\nompyr\.tmp_api_commit\AnimeKAI-API-387dcdb7664499b405c804520e93d68c653b4487\app.py
```

Then run the frontend with:

```bash
npm run dev
```

The adapter currently uses the zip for homepage metadata, details, and episode rows. Direct stream and download resolution remain disabled in the frontend prototype.

## Next Production Steps

1. Move the static UI into Astro 5 islands with React components where state is needed.
2. Replace demo data with a Cloudflare Worker API.
3. Add a D1 schema for users, favorites, history, watchlists, sources, and analytics.
4. Add Upstash Redis caching around home, search, details, episodes, streams, and downloads.
5. Connect Supabase Auth for synced history and favorites.
6. Add CSP, rate limiting, request validation, Sentry, sitemap, robots, RSS, and OpenGraph generation.
