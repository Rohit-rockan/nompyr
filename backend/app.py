import re
import time
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import scrapers
from scrapers import (
    search_anime,
    scrape_home,
    scrape_anime_info,
    fetch_episodes,
    fetch_servers,
    resolve_source,
    scrape_most_searched,
    search_anime_miruro,
    scrape_home_miruro,
    scrape_anime_info_miruro,
    fetch_episodes_miruro,
    fetch_servers_miruro,
    resolve_source_miruro,
    search_anime_aniwatch,
    scrape_home_aniwatch,
    scrape_anime_info_aniwatch,
    fetch_episodes_aniwatch,
    fetch_servers_aniwatch,
    search_anime_hanime,
    scrape_home_hanime,
    scrape_anime_info_hanime,
    fetch_episodes_hanime,
    fetch_servers_hanime,
    resolve_hanime_source
)

# Import recommender
from recommender import AnimeRecommender, find_local_slug_by_title

app = Flask(__name__)
CORS(app)

anime_recommender = AnimeRecommender()

# ─── Simple In-Memory Thread-Safe Cache ─────────────────────────────────────
class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                val, expires = self._cache[key]
                if time.time() < expires:
                    return val
                else:
                    del self._cache[key]
            return None

    def set(self, key, value, timeout=300):
        expires = time.time() + timeout
        with self._lock:
            self._cache[key] = (value, expires)

    def clear(self):
        with self._lock:
            self._cache.clear()

cache = SimpleCache()

# ─── Helper Functions ────────────────────────────────────────────────────────
def prefix_item(item, source):
    if not item: return item
    item = dict(item)
    slug = item.get("slug", "")
    if slug and not str(slug).startswith(f"{source}:"):
        item["slug"] = f"{source}:{slug}"
    
    item_id = item.get("id") or slug
    if item_id and not str(item_id).startswith(f"{source}:"):
        item["id"] = f"{source}:{item_id}"
    return item

def merge_lists(*lists):
    merged = []
    max_len = max(len(l) for l in lists) if lists else 0
    for i in range(max_len):
        for l in lists:
            if i < len(l):
                merged.append(l[i])
    return merged

def safe_run(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error executing {func.__name__}: {e}")
        return {}

def parse_release_date_safe(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y", "%B %d, %Y"):
        try:
            return time.strptime(date_str, fmt)
        except ValueError:
            pass
    match = re.search(r'\b(19\d\d|20\d\d)\b', date_str)
    if match:
        try:
            return time.strptime(match.group(1), "%Y")
        except ValueError:
            pass
    return None

def get_score_val(item):
    val = item.get("score") or item.get("mal_score") or item.get("rating") or "N/A"
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def matches_language(item, lang):
    lang = lang.lower()
    languages = [l.lower() for l in (item.get("language") or [])]
    has_sub = "sub" in languages or bool(item.get("sub_episodes")) or any("sub" in str(s).lower() for s in languages)
    has_dub = "dub" in languages or bool(item.get("dub_episodes")) or any("dub" in str(s).lower() for s in languages)
    if lang == "sub":
        return has_sub
    elif lang == "dub":
        return has_dub
    elif lang == "sub & dub" or lang == "both":
        return has_sub and has_dub
    return True

def matches_genre(item, g):
    item_genres = [str(genre).lower() for genre in (item.get("genres") or [])]
    if any(g in genre for genre in item_genres):
        return True
    return g in str(item.get("type", "")).lower() or g in str(item.get("title", "")).lower() or g in str(item.get("japanese_title", "")).lower() or g in str(item.get("slug", "")).lower()

def matches_date_range(item, start_year, start_month, start_day, end_year, end_month, end_day):
    date_str = item.get("year") or item.get("release") or item.get("detail", {}).get("released") or item.get("detail", {}).get("premiered") or ""
    item_t = parse_release_date_safe(date_str)
    if not item_t:
        try:
            year_val = int(item.get("year") or date_str[:4])
            if start_year and year_val < int(start_year):
                return False
            if end_year and year_val > int(end_year):
                return False
            return True
        except Exception:
            return True
            
    if start_year:
        try:
            st = time.struct_time((int(start_year), int(start_month or 1), int(start_day or 1), 0, 0, 0, 0, 0, -1))
            if item_t < st:
                return False
        except Exception:
            pass
            
    if end_year:
        try:
            et = time.struct_time((int(end_year), int(end_month or 12), int(end_day or 31), 23, 59, 59, 0, 0, -1))
            if item_t > et:
                return False
        except Exception:
            pass
            
    return True

def get_year_val(item):
    year_str = item.get("year") or ""
    try:
        match = re.search(r'\b(19\d\d|20\d\d)\b', str(year_str))
        if match:
            return int(match.group(1))
        date_str = item.get("release") or item.get("detail", {}).get("released") or item.get("detail", {}).get("premiered") or ""
        match = re.search(r'\b(19\d\d|20\d\d)\b', str(date_str))
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 0

def clean_search_title(title):
    if not title:
        return []
        
    extra_variants = []
    if "..." in title:
        parts = title.split("...")
        first_part = parts[0].strip()
        words_first = first_part.split()
        if len(words_first) > 1:
            clean_prefix = " ".join(words_first[:-1])
            clean_prefix = re.sub(r'[^a-zA-Z0-9\s]+$', '', clean_prefix).strip()
            if clean_prefix:
                extra_variants.append(clean_prefix)
        elif words_first:
            clean_prefix = re.sub(r'[^a-zA-Z0-9\s]+$', '', words_first[0]).strip()
            if clean_prefix:
                extra_variants.append(clean_prefix)

    # Remove common tags in brackets/parentheses like (Dub), (Sub), [Uncensored], [1080p], etc.
    tag_pattern = r'[\(\[\{](?:dub|sub|uncensored|uncut|batch|multi-sub|split cour|1080p|720p|h264|hevc|x264|x265|bluray|bd|web-dl|web|dvd|tv|movie|ova|ona|special)[\)\]\}]'
    title_cleaned = re.sub(tag_pattern, '', title, flags=re.IGNORECASE)
    
    # Strip double and single quotes
    title_cleaned = title_cleaned.replace('"', '').replace("'", "")
    
    # Remove bracket symbols but keep their contents
    title_cleaned = title_cleaned.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '').replace('【', '').replace('】', '')
    
    # Replace ... with space
    title_cleaned = re.sub(r'\.\.\.+', ' ', title_cleaned)
    
    # Normalize spaces
    title_cleaned = re.sub(r'\s+', ' ', title_cleaned).strip()
    
    variants = []
    
    # Add extra variants first
    for ev in extra_variants:
        if ev.lower() not in [v.lower() for v in variants]:
            variants.append(ev)
            
    # Variant 1: Cleaned title
    if title_cleaned:
        variants.append(title_cleaned)
        
    # Variant 2: Cleaned title without season/part suffixes
    no_season = re.sub(r'\b\d+(st|nd|rd|th)?\s+season\b', '', title_cleaned, flags=re.IGNORECASE)
    no_season = re.sub(r'\bseason\s+\d+\b', '', no_season, flags=re.IGNORECASE)
    no_season = re.sub(r'\bpart\s+\d+\b', '', no_season, flags=re.IGNORECASE)
    no_season = re.sub(r'\bpart\s+[i|v|x]+\b', '', no_season, flags=re.IGNORECASE)
    no_season = re.sub(r'\s+', ' ', no_season).strip()
    if no_season and no_season.lower() != title_cleaned.lower():
        variants.append(no_season)
        
    # Variant 3: Split by common separators
    for separator in (':', '-', '–', '—', ','):
        if separator in title_cleaned:
            parts = title_cleaned.split(separator)
            first_part = parts[0].strip()
            if first_part and len(first_part.split()) >= 2:
                variants.append(first_part)
                
    # Variant 4: Truncate to first N words
    words = title_cleaned.split()
    if len(words) > 6:
        variants.append(" ".join(words[:6]))
    if len(words) > 4:
        variants.append(" ".join(words[:4]))
    if len(words) > 2:
        variants.append(" ".join(words[:2]))
        
    # Deduplicate variants while preserving order
    seen = set()
    deduped = []
    for v in variants:
        if v and v.lower() not in seen:
            seen.add(v.lower())
            deduped.append(v)
            
    return deduped

def get_anilist_metadata(title):
    if not title:
        return {"poster": "", "score": "N/A"}
        
    cache_key = f"metadata:{title.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    variants = clean_search_title(title)
    if not variants:
        res = {"poster": "", "score": "N/A"}
        cache.set(cache_key, res, timeout=86400)
        return res
        
    # Build GraphQL query dynamically based on number of variants (limit to max 4 variants)
    variants = variants[:4]
    
    query_args = ", ".join(f"$s{i}: String" for i in range(len(variants)))
    query_body = ""
    for i in range(len(variants)):
        query_body += f"""
        q{i}: Page(page: 1, perPage: 1) {{
            media(search: $s{i}, type: ANIME) {{
                coverImage {{
                    extraLarge
                    large
                }}
                averageScore
            }}
        }}
        """
        
    query = f"query ({query_args}) {{ {query_body} }}"
    variables = {f"s{i}": variants[i] for i in range(len(variants))}
    
    try:
        url = "https://graphql.anilist.co"
        import requests as _requests
        r = _requests.post(url, json={"query": query, "variables": variables}, headers={"User-Agent": "Mozilla/5.0"}, timeout=4.0)
        if r.status_code == 200:
            data = r.json().get("data", {})
            for i in range(len(variants)):
                media_list = data.get(f"q{i}", {}).get("media", [])
                if media_list and media_list[0]:
                    media = media_list[0]
                    cover = media.get("coverImage", {}).get("extraLarge") or media.get("coverImage", {}).get("large") or ""
                    score = media.get("averageScore")
                    score_str = f"{score/10:.1f}" if score is not None else "N/A"
                    res = {"poster": cover, "score": score_str}
                    cache.set(cache_key, res, timeout=86400 * 7) # Cache successful hit for 7 days
                    return res
    except Exception as e:
        print(f"Error fetching AniList metadata for {title}: {e}")
        
    res = {"poster": "", "score": "N/A"}
    cache.set(cache_key, res, timeout=86400) # Cache negative hit for 1 day
    return res


def fetch_single_batch(batch, batch_idx):
    query_variables = {}
    query_args_list = []
    query_body_parts = []
    valid_batch_indices = []
    
    for idx, title_item in enumerate(batch):
        variants = clean_search_title(title_item)
        if not variants:
            continue
            
        variants = variants[:2] # Limit to top 2 variants per title
        valid_batch_indices.append((idx, title_item, variants))
        
        for v_idx, variant in enumerate(variants):
            var_name = f"b{idx}_v{v_idx}"
            query_args_list.append(f"${var_name}: String")
            query_variables[var_name] = variant
            
            alias_name = f"alias_{idx}_{v_idx}"
            query_body_parts.append(f"""
            {alias_name}: Page(page: 1, perPage: 1) {{
                media(search: ${var_name}, type: ANIME) {{
                    coverImage {{
                        extraLarge
                        large
                    }}
                    averageScore
                }}
            }}
            """)
            
    if not query_body_parts:
        return {}
        
    query_args_str = ", ".join(query_args_list)
    query_body_str = "\n".join(query_body_parts)
    query = f"query ({query_args_str}) {{ {query_body_str} }}"
    
    batch_results = {}
    try:
        url = "https://graphql.anilist.co"
        import requests as _requests
        r = _requests.post(url, json={"query": query, "variables": query_variables}, headers={"User-Agent": "Mozilla/5.0"}, timeout=6.0)
        if r.status_code == 200:
            data = r.json().get("data", {}) or {}
            for idx, title_item, variants in valid_batch_indices:
                resolved_meta = None
                for v_idx in range(len(variants)):
                    alias_name = f"alias_{idx}_{v_idx}"
                    media_list = data.get(alias_name, {}).get("media", [])
                    if media_list and media_list[0]:
                        media = media_list[0]
                        cover = media.get("coverImage", {}).get("extraLarge") or media.get("coverImage", {}).get("large") or ""
                        score = media.get("averageScore")
                        score_str = f"{score/10:.1f}" if score is not None else "N/A"
                        resolved_meta = {"poster": cover, "score": score_str}
                        break
                if resolved_meta:
                    batch_results[title_item] = resolved_meta
                else:
                    batch_results[title_item] = {"poster": "", "score": "N/A"}
        else:
            print(f"GraphQL batch request failed with status code {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Error executing batch query: {e}")
        
    return batch_results


def get_anilist_metadata_batch(titles):
    if not titles:
        return {}
        
    results = {}
    uncached_titles = []
    
    # 1. Check cache first
    for title in titles:
        if not title:
            continue
        cache_key = f"metadata:{title.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            results[title] = cached
        else:
            if title not in uncached_titles:
                uncached_titles.append(title)
            
    if not uncached_titles:
        return results
        
    # 2. Query uncached titles in batches of 10 concurrently
    batch_size = 10
    batches = [uncached_titles[i:i+batch_size] for i in range(0, len(uncached_titles), batch_size)]
    
    # Execute batch requests concurrently using the pre-imported ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_single_batch, batch, idx) for idx, batch in enumerate(batches)]
        for fut in futures:
            try:
                batch_res = fut.result()
                if batch_res:
                    for title, meta in batch_res.items():
                        results[title] = meta
                        cache_key = f"metadata:{title.lower()}"
                        ttl = 86400 * 7 if meta.get("poster") else 86400
                        cache.set(cache_key, meta, timeout=ttl)
            except Exception as e:
                print(f"Error in batch future resolution: {e}")
                
    # Fill remaining uncached missing entries
    for title in uncached_titles:
        if title not in results:
            results[title] = {"poster": "", "score": "N/A"}
            
    return results


def enrich_results(results):
    if not results:
        return results
        
    to_enrich_indices = []
    titles_to_enrich = []
    
    for idx, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        poster = item.get("poster", "")
        score = item.get("score") or item.get("mal_score") or "N/A"
        slug = item.get("slug", "")
        
        is_hanime = False
        if slug and str(slug).startswith("hanime:"):
            is_hanime = True
        if poster and ("hanime-cdn.com" in poster or "hanime.tv" in poster or "htv-services.com" in poster):
            is_hanime = True
            
        needs_enrich = False
        if score == "N/A" or not score:
            needs_enrich = True
        if not poster or "animeverse.to/i/" in poster or "nekkoto" in poster:
            needs_enrich = True
        if is_hanime:
            needs_enrich = True
            
        if needs_enrich:
            title = item.get("title", "")
            if title:
                to_enrich_indices.append(idx)
                titles_to_enrich.append(title)
                
    if not titles_to_enrich:
        return results
        
    # Retrieve enriched metadata in batch
    enriched_data = get_anilist_metadata_batch(titles_to_enrich)
    
    for idx, title in zip(to_enrich_indices, titles_to_enrich):
        meta = enriched_data.get(title)
        if meta:
            orig_poster = results[idx].get("poster", "")
            is_orig_hanime = False
            if orig_poster and ("hanime-cdn.com" in orig_poster or "hanime.tv" in orig_poster or "htv-services.com" in orig_poster):
                is_orig_hanime = True
                
            if meta.get("poster") and (not orig_poster or "animeverse.to/i/" in orig_poster or "nekkoto" in orig_poster or is_orig_hanime):
                results[idx]["poster"] = meta["poster"]
            if meta.get("score") and meta["score"] != "N/A":
                results[idx]["score"] = meta["score"]
                results[idx]["mal_score"] = meta["score"]
                
    return results



# ─── API Routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "success": True,
        "api": "Nompyr REST API",
        "version": "1.2.0",
        "endpoints": {
            "/api/home": "Get banner, latest updates, and trending (Cached)",
            "/api/most-searched": "Get most-searched anime keywords (Cached)",
            "/api/search?keyword=...": "Search anime (Cached)",
            "/api/anime/<slug>": "Get anime details (Cached)",
            "/api/episodes/<ani_id>": "Get episode list (Cached)",
            "/api/servers/<ep_token>": "Get available servers for an episode (Cached)",
            "/api/source/<path:link_id>": "Get direct stream sources (Cached)",
            "/api/cache/clear": "Clear in-memory cache"
        }
    })

@app.route("/api/cache/clear", methods=["GET", "POST"])
def clear_api_cache():
    cache.clear()
    return jsonify({"success": True, "message": "In-memory cache cleared successfully."})

@app.route("/api/proxy-image", methods=["GET"])
def proxy_image():
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://hanime.tv/"
    }
    
    try:
        import requests as _requests
        r = _requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "image/jpeg")
        
        from flask import Response
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk
        return Response(generate(), content_type=content_type)
    except Exception as e:
        return f"Error fetching image: {str(e)}", 500

@app.route("/api/search-predictions", methods=["GET"])
def api_search_predictions():
    return jsonify([])

@app.route("/api/recommendations/description", methods=["GET"])
def api_recommend_description():
    return jsonify({"success": True, "results": []})

@app.route("/api/recommendations/anime", methods=["GET"])
def api_recommend_anime():
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "Anime title is required"}), 400
        
    cache_key = f"recs_anime:{title}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    recommendations = []
    try:
        search_url = f"https://api.jikan.moe/v4/anime"
        r = requests.get(search_url, params={"q": title, "limit": 1}, timeout=10)
        if r.status_code == 200:
            search_data = r.json().get("data", [])
            if search_data:
                mal_id = search_data[0].get("mal_id")
                
                recs_url = f"https://api.jikan.moe/v4/anime/{mal_id}/recommendations"
                r_recs = requests.get(recs_url, timeout=10)
                if r_recs.status_code == 200:
                    recs_data = r_recs.json().get("data", [])
                    for rec in recs_data[:12]:
                        entry = rec.get("entry", {})
                        rec_title = entry.get("title", "")
                        rec_images = entry.get("images", {}).get("jpg", {}).get("image_url", "")
                        
                        local_slug = find_local_slug_by_title(rec_title)
                        
                        recommendations.append({
                            "title": rec_title,
                            "japanese_title": "",
                            "slug": local_slug or f"search-fallback:{rec_title}",
                            "id": local_slug or f"search-fallback:{rec_title}",
                            "poster": rec_images,
                            "sub_episodes": "1",
                            "dub_episodes": "",
                            "total_episodes": "1",
                            "year": "",
                            "type": "TV",
                            "rating": "",
                            "score": "N/A"
                        })
    except Exception as e:
        print("Error fetching Jikan recommendations:", e)
        
    # No local catalog fallback after removing animeverse
                
    res = {"success": True, "results": recommendations}
    cache.set(cache_key, res, timeout=1800)
    return jsonify(res)

@app.route("/api/most-searched", methods=["GET"])
def api_most_searched_endpoint():
    cached = cache.get("most_searched")
    if cached is not None:
        return jsonify(cached)
        
    res = scrape_most_searched()
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    response_data = {"success": True, "count": len(res), "results": res}
    if "error" not in response_data:
        cache.set("most_searched", response_data, timeout=1800)
    return jsonify(response_data)

@app.route("/api/search", methods=["GET"])
def api_search():
    kw = request.args.get("keyword", "").strip()
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    source = request.args.get("source", "").strip().lower()
    
    genre = request.args.get("genre", "").strip().lower()
    atype = request.args.get("type", "").strip().lower()
    status = request.args.get("status", "").strip().lower()
    year = request.args.get("year", "").strip().lower()
    rating = request.args.get("rating", "").strip().lower()
    score = request.args.get("score", "").strip().lower()
    season = request.args.get("season", "").strip().lower()
    language = request.args.get("language", "").strip().lower()
    start_year = request.args.get("start_year", "").strip().lower()
    start_month = request.args.get("start_month", "").strip().lower()
    start_day = request.args.get("start_day", "").strip().lower()
    end_year = request.args.get("end_year", "").strip().lower()
    end_month = request.args.get("end_month", "").strip().lower()
    end_day = request.args.get("end_day", "").strip().lower()
    sort = request.args.get("sort", "").strip().lower()
    genres = request.args.get("genres", "").strip().lower()

    # Create search cache key
    cache_key = f"search:{kw}:{page}:{source}:{genre}:{atype}:{status}:{year}:{rating}:{score}:{season}:{language}:{start_year}:{start_month}:{start_day}:{end_year}:{end_month}:{end_day}:{sort}:{genres}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
    
    if source == "animekai":
        res = search_anime(kw, page)
    elif source == "aniwatch":
        res = search_anime_aniwatch(kw, page)
    elif source == "hanime":
        res = search_anime_hanime(kw, page)
    elif source == "miruro":
        res = search_anime_miruro(kw, page)
    elif source == "all" or not source:
        with ThreadPoolExecutor(max_workers=4) as executor:
            fut_kai = executor.submit(safe_run, search_anime, kw, page)
            fut_watch = executor.submit(safe_run, search_anime_aniwatch, kw, page)
            fut_hanime = executor.submit(safe_run, search_anime_hanime, kw, page)
            fut_miruro = executor.submit(safe_run, search_anime_miruro, kw, page)
            
            res_kai = fut_kai.result()
            res_watch = fut_watch.result()
            res_hanime = fut_hanime.result()
            res_miruro = fut_miruro.result()
            
        def clean_res(r):
            if isinstance(r, tuple): return {}
            if isinstance(r, dict) and "error" in r: return {}
            return r or {}
            
        kai = clean_res(res_kai)
        watch = clean_res(res_watch)
        hanime = clean_res(res_hanime)
        miruro = clean_res(res_miruro)
        
        def prefix_list(lst, prefix):
            return [prefix_item(item, prefix) for item in lst] if lst else []
            
        results = merge_lists(
            prefix_list(kai.get("results", []), "animekai"),
            prefix_list(watch.get("results", []), "aniwatch"),
            prefix_list(hanime.get("results", []), "hanime"),
            prefix_list(miruro.get("results", []), "miruro")
        )
        
        total = (kai.get("total", 0) or 0) + (watch.get("total", 0) or 0) + (hanime.get("total", 0) or 0) + (miruro.get("total", 0) or 0)
        
        res = {
            "results": results,
            "total": total,
            "page": page,
            "per_page": len(results)
        }
    else:
        res = search_anime(kw, page)

    if isinstance(res, dict) and "results" in res:
        results = res["results"]
        if genre:
            results = [item for item in results if genre in str(item.get("genres", [])).lower() or genre in str(item.get("type", "")).lower() or genre in str(item.get("title", "")).lower() or genre in str(item.get("japanese_title", "")).lower() or genre in str(item.get("slug", "")).lower()]
        if atype:
            results = [item for item in results if atype in str(item.get("type", "")).lower()]
        if status:
            results = [item for item in results if status in str(item.get("status", "")).lower()]
        if year:
            results = [item for item in results if year in str(item.get("year", "")).lower()]
        if rating:
            results = [item for item in results if rating in str(item.get("rating", "")).lower() or rating in str(item.get("ratingLabel", "")).lower()]
        if score:
            try:
                min_score = float(score)
                results = [item for item in results if get_score_val(item) >= min_score]
            except ValueError:
                pass
        if season:
            results = [item for item in results if season in str(item.get("season", "")).lower() or season in str(item.get("premiered", "")).lower() or season in str(item.get("release", "")).lower()]
        if language:
            results = [item for item in results if matches_language(item, language)]
        if start_year or end_year or start_month or end_month or start_day or end_day:
            results = [item for item in results if matches_date_range(item, start_year, start_month, start_day, end_year, end_month, end_day)]
        if genres:
            genre_list = [g.strip().lower() for g in genres.split(",") if g.strip()]
            for g in genre_list:
                results = [item for item in results if matches_genre(item, g)]
                
        if sort:
            if sort == "title_asc":
                results.sort(key=lambda x: str(x.get("title", "")).lower())
            elif sort == "title_desc":
                results.sort(key=lambda x: str(x.get("title", "")).lower(), reverse=True)
            elif sort == "score_desc":
                results.sort(key=get_score_val, reverse=True)
            elif sort == "year_desc":
                results.sort(key=lambda x: get_year_val(x), reverse=True)
            elif sort == "year_asc":
                results.sort(key=lambda x: get_year_val(x))
            elif sort == "latest_desc":
                results.sort(key=lambda x: str(x.get("updatedAt", "") or x.get("updated", "")), reverse=True)
                
        res["results"] = enrich_results(results)
        res["total"] = len(res["results"])
        res["per_page"] = len(res["results"])

    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=300) # cache search for 5 minutes
    return jsonify(final_res)

@app.route("/api/home", methods=["GET"])
def api_home():
    source = request.args.get("source", "").strip().lower()
    
    cache_key = f"home:{source}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    if source == "animekai":
        res = scrape_home()
    elif source == "aniwatch":
        res = scrape_home_aniwatch()
    elif source == "hanime":
        res = scrape_home_hanime()
    elif source == "miruro":
        res = scrape_home_miruro()
    elif source == "all" or not source:
        with ThreadPoolExecutor(max_workers=4) as executor:
            fut_kai = executor.submit(safe_run, scrape_home)
            fut_watch = executor.submit(safe_run, scrape_home_aniwatch)
            fut_hanime = executor.submit(safe_run, scrape_home_hanime)
            fut_miruro = executor.submit(safe_run, scrape_home_miruro)
            
            res_kai = fut_kai.result()
            res_watch = fut_watch.result()
            res_hanime = fut_hanime.result()
            res_miruro = fut_miruro.result()
            
        def clean_res(r):
            if isinstance(r, tuple): return {}
            if isinstance(r, dict) and "error" in r: return {}
            return r or {}
            
        kai = clean_res(res_kai)
        watch = clean_res(res_watch)
        hanime = clean_res(res_hanime)
        miruro = clean_res(res_miruro)
        
        def prefix_list(lst, prefix):
            return [prefix_item(item, prefix) for item in lst] if lst else []
            
        banners = merge_lists(
            prefix_list(kai.get("banner", []), "animekai"),
            prefix_list(watch.get("banner", []), "aniwatch"),
            prefix_list(hanime.get("banner", []), "hanime"),
            prefix_list(miruro.get("banner", []), "miruro")
        )
        
        latest = merge_lists(
            prefix_list(kai.get("latest_updates", []), "animekai"),
            prefix_list(watch.get("latest_updates", []), "aniwatch"),
            prefix_list(hanime.get("latest_updates", []), "hanime"),
            prefix_list(miruro.get("latest_updates", []), "miruro")
        )
        
        t_kai = kai.get("top_trending", {})
        t_watch = watch.get("top_trending", {})
        t_hanime = hanime.get("top_trending", {})
        t_miruro = miruro.get("top_trending", {})
        
        trending = {}
        for key in ["NOW", "DAY", "WEEK", "MONTH"]:
            trending[key] = merge_lists(
                prefix_list(t_kai.get(key, []), "animekai"),
                prefix_list(t_watch.get(key, []), "aniwatch"),
                prefix_list(t_hanime.get(key, []), "hanime"),
                prefix_list(t_miruro.get(key, []), "miruro")
            )
            
        popular = merge_lists(
            prefix_list(kai.get("popular", []), "animekai"),
            prefix_list(watch.get("popular", []), "aniwatch"),
            prefix_list(hanime.get("popular", []), "hanime"),
            prefix_list(miruro.get("popular", []), "miruro")
        )
        
        upcoming = merge_lists(
            prefix_list(kai.get("upcoming", []), "animekai"),
            prefix_list(watch.get("upcoming", []), "aniwatch"),
            prefix_list(hanime.get("upcoming", []), "hanime"),
            prefix_list(miruro.get("upcoming", []), "miruro")
        )
        
        res = {
            "banner": banners,
            "latest_updates": latest,
            "top_trending": trending,
            "popular": popular,
            "upcoming": upcoming
        }
    else:
        res = scrape_home()
        
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    if isinstance(res, dict):
        # Prefetch all metadata in one parallel batch call to warm up the cache
        all_items = []
        if "banner" in res and res["banner"]:
            all_items.extend(res["banner"])
        if "latest_updates" in res and res["latest_updates"]:
            all_items.extend(res["latest_updates"])
        if "popular" in res and res["popular"]:
            all_items.extend(res["popular"])
        if "upcoming" in res and res["upcoming"]:
            all_items.extend(res["upcoming"])
        if "top_trending" in res and isinstance(res["top_trending"], dict):
            for key in res["top_trending"]:
                if res["top_trending"][key]:
                    all_items.extend(res["top_trending"][key])
                    
        titles_to_prefetch = []
        for item in all_items:
            if not isinstance(item, dict):
                continue
            poster = item.get("poster", "")
            score = item.get("score") or item.get("mal_score") or "N/A"
            
            needs_enrich = False
            if score == "N/A" or not score:
                needs_enrich = True
            if not poster or "animeverse.to/i/" in poster or "nekkoto" in poster:
                needs_enrich = True
                
            if needs_enrich:
                title = item.get("title", "")
                if title and title not in titles_to_prefetch:
                    titles_to_prefetch.append(title)
                    
        if titles_to_prefetch:
            get_anilist_metadata_batch(titles_to_prefetch)

        if "banner" in res:
            res["banner"] = enrich_results(res["banner"])
        if "latest_updates" in res:
            res["latest_updates"] = enrich_results(res["latest_updates"])
        if "popular" in res:
            res["popular"] = enrich_results(res["popular"])
        if "upcoming" in res:
            res["upcoming"] = enrich_results(res["upcoming"])
        if "top_trending" in res and isinstance(res["top_trending"], dict):
            for key in res["top_trending"]:
                res["top_trending"][key] = enrich_results(res["top_trending"][key])
                
    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=600) # Cache home for 10 minutes
    return jsonify(final_res)

@app.route("/api/anime/<slug>", methods=["GET"])
def api_anime_info(slug):
    cache_key = f"anime:{slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    source = None
    stripped_slug = slug
    
    if slug.startswith("hanime:"):
        source = "hanime"
        stripped_slug = slug.split("hanime:", 1)[1]
    elif slug.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_slug = slug.split("aniwatch:", 1)[1]
    elif slug.startswith("animekai:"):
        source = "animekai"
        stripped_slug = slug.split("animekai:", 1)[1]
    elif slug.startswith("miruro:"):
        source = "miruro"
        stripped_slug = slug.split("miruro:", 1)[1]
    else:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"
            
    if source == "aniwatch":
        res = scrape_anime_info_aniwatch(stripped_slug)
    elif source == "hanime":
        res = scrape_anime_info_hanime(stripped_slug)
    elif source == "miruro":
        res = scrape_anime_info_miruro(stripped_slug)
    else:
        res = scrape_anime_info(stripped_slug)
        
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    if isinstance(res, dict) and "ani_id" in res:
        if not str(res["ani_id"]).startswith(f"{source}:"):
            res["ani_id"] = f"{source}:{res['ani_id']}"
            
    if isinstance(res, dict) and "error" not in res:
        poster = res.get("poster", "")
        score = res.get("mal_score") or res.get("score") or "N/A"
        
        is_hanime = False
        if source == "hanime":
            is_hanime = True
        if poster and ("hanime-cdn.com" in poster or "hanime.tv" in poster or "htv-services.com" in poster):
            is_hanime = True
            
        needs_enrich = False
        if score == "N/A" or not score:
            needs_enrich = True
        if not poster or "animeverse.to/i/" in poster or "nekkoto" in poster:
            needs_enrich = True
        if is_hanime:
            needs_enrich = True
            
        if needs_enrich:
            meta = get_anilist_metadata(res.get("title", ""))
            if meta:
                is_orig_hanime = False
                if poster and ("hanime-cdn.com" in poster or "hanime.tv" in poster or "htv-services.com" in poster):
                    is_orig_hanime = True
                    
                if meta.get("poster") and (not poster or "animeverse.to/i/" in poster or "nekkoto" in poster or is_orig_hanime):
                    res["poster"] = meta["poster"]
                    res["banner"] = meta["poster"]
                if meta.get("score") and meta["score"] != "N/A":
                    score = meta["score"]
                    if "detail" in res and isinstance(res["detail"], dict):
                        res["detail"]["score"] = meta["score"]
                        
        if score and score != "N/A":
            res["score"] = score
            res["mal_score"] = score
            
    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=900) # Cache details for 15 minutes
    return jsonify(final_res)

@app.route("/api/episodes/<ani_id>", methods=["GET"])
def api_episodes(ani_id):
    cache_key = f"episodes:{ani_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    source = None
    stripped_id = ani_id
    
    if ani_id.startswith("hanime:"):
        source = "hanime"
        stripped_id = ani_id.split("hanime:", 1)[1]
    elif ani_id.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_id = ani_id.split("aniwatch:", 1)[1]
    elif ani_id.startswith("animekai:"):
        source = "animekai"
        stripped_id = ani_id.split("animekai:", 1)[1]
    elif ani_id.startswith("miruro:"):
        source = "miruro"
        stripped_id = ani_id.split("miruro:", 1)[1]
    else:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"
            
    if source == "aniwatch":
        res = fetch_episodes_aniwatch(stripped_id)
    elif source == "hanime":
        res = fetch_episodes_hanime(stripped_id)
    elif source == "miruro":
        res = fetch_episodes_miruro(stripped_id)
    else:
        res = fetch_episodes(stripped_id)
        
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    if isinstance(res, list):
        prefixed_eps = []
        for ep in res:
            ep_copy = dict(ep)
            if "token" in ep_copy and ep_copy["token"]:
                if not str(ep_copy["token"]).startswith(f"{source}:"):
                    ep_copy["token"] = f"{source}:{ep_copy['token']}"
            else:
                ep_copy["token"] = f"{source}:{stripped_id}:ep-{ep_copy.get('number', '1')}"
            prefixed_eps.append(ep_copy)
        res = prefixed_eps
        
    final_res = {"success": True, "ani_id": ani_id, "count": len(res), "episodes": res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=600) # Cache episodes list for 10 minutes
    return jsonify(final_res)

@app.route("/api/servers/<ep_token>", methods=["GET"])
def api_servers(ep_token):
    cache_key = f"servers:{ep_token}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    source = None
    stripped_token = ep_token
    
    if ep_token.startswith("hanime:"):
        source = "hanime"
    elif ep_token.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_token = ep_token.split("aniwatch:", 1)[1]
    elif ep_token.startswith("animekai:"):
        source = "animekai"
        stripped_token = ep_token.split("animekai:", 1)[1]
    elif ep_token.startswith("miruro:"):
        source = "miruro"
        stripped_token = ep_token.split("miruro:", 1)[1]
    else:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"
            
    if source == "aniwatch":
        res = fetch_servers_aniwatch(stripped_token)
    elif source == "hanime":
        res = fetch_servers_hanime(ep_token)
    elif source == "miruro":
        res = fetch_servers_miruro(ep_token)
    else:
        res = fetch_servers(stripped_token)
        
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    if isinstance(res, dict) and "servers" in res:
        for lang in res["servers"]:
            prefixed_srvs = []
            for srv in res["servers"][lang]:
                srv_copy = dict(srv)
                if "link_id" in srv_copy and srv_copy["link_id"]:
                    if not str(srv_copy["link_id"]).startswith(f"{source}:"):
                        srv_copy["link_id"] = f"{source}:{srv_copy['link_id']}"
                prefixed_srvs.append(srv_copy)
            res["servers"][lang] = prefixed_srvs
            
    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=300) # Cache servers list for 5 minutes
    return jsonify(final_res)

def get_base_origin(url):
    if not url:
        return ""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass
    return ""

@app.route("/api/proxy-hls", methods=["GET"])
@app.route("/api/proxy-hls/stream.m3u8", methods=["GET"])
def proxy_hls():
    url = request.args.get("url")
    referer = request.args.get("referer")
    if not url:
        return "Missing url parameter", 400
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if referer:
        base_ref = get_base_origin(referer)
        if base_ref:
            headers["Referer"] = base_ref
            
    is_playlist = url.split("?")[0].endswith(".m3u8") or ".m3u8" in url.lower()
    
    try:
        import requests as _requests
        if is_playlist:
            r = _requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                return f"Proxy error: status {r.status_code}", r.status_code
                
            content = r.text
            base_url = url.rsplit("/", 1)[0] + "/"
            
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("#"):
                    new_lines.append(line)
                else:
                    if not line_str.startswith("http://") and not line_str.startswith("https://"):
                        resolved_url = base_url + line_str
                    else:
                        resolved_url = line_str
                        
                    is_line_playlist = resolved_url.split("?")[0].endswith(".m3u8") or ".m3u8" in resolved_url.lower()
                    from urllib.parse import quote
                    path_suffix = "/stream.m3u8" if is_line_playlist else ""
                    proxied_url = f"{request.host_url}api/proxy-hls{path_suffix}?url={quote(resolved_url)}"
                    if referer:
                        proxied_url += f"&referer={quote(referer)}"
                    new_lines.append(proxied_url)
                    
            rewritten_m3u8 = "\n".join(new_lines)
            response = app.response_class(
                response=rewritten_m3u8,
                status=200,
                mimetype="application/vnd.apple.mpegurl"
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
        else:
            # Proxy binary media segment (.ts or others)
            r = _requests.get(url, headers=headers, stream=True, timeout=15)
            if r.status_code != 200:
                return f"Segment Proxy error: status {r.status_code}", r.status_code
                
            def generate_bytes():
                for chunk in r.iter_content(chunk_size=40960):
                    yield chunk
                    
            response = app.response_class(
                response=generate_bytes(),
                status=200,
                mimetype=r.headers.get("Content-Type", "video/MP2T")
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
            
    except Exception as e:
        return f"Proxy exception: {e}", 500

@app.route("/api/proxy-player", methods=["GET"])
def proxy_player():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://hanime.tv/"
    }
    try:
        import requests as _requests
        r = _requests.get("https://player.hanime.tv/", headers=headers, timeout=10)
        if r.status_code != 200:
            return f"Proxy error: status {r.status_code}", r.status_code
        
        html = r.text
        # Rewrite relative assets to absolute URLs pointing to player.hanime.tv
        html = html.replace('src="/', 'src="https://player.hanime.tv/')
        html = html.replace('href="/', 'href="https://player.hanime.tv/')
        html = html.replace('src="js/', 'src="https://player.hanime.tv/js/')
        html = html.replace('href="js/', 'href="https://player.hanime.tv/js/')
        html = html.replace('href="css/', 'href="https://player.hanime.tv/css/')
        html = html.replace('href="fonts/', 'href="https://player.hanime.tv/fonts/')
        html = html.replace('src="img/', 'src="https://player.hanime.tv/img/')
        
        response = app.response_class(
            response=html,
            status=200,
            mimetype="text/html"
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        # This proxy has no Content-Security-Policy or X-Frame-Options, permitting local embedding
        return response
    except Exception as e:
        return f"Proxy exception: {e}", 500

@app.route("/api/source/<path:link_id>", methods=["GET"])
def api_source(link_id):
    cache_key = f"source:{link_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    source = None
    stripped_link = link_id
    
    if link_id.startswith("hanime:"):
        source = "hanime"
    elif link_id.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_link = link_id.split("aniwatch:", 1)[1]
    elif link_id.startswith("animekai:"):
        source = "animekai"
        stripped_link = link_id.split("animekai:", 1)[1]
    elif link_id.startswith("miruro:"):
        source = "miruro"
        stripped_link = link_id.split("miruro:", 1)[1]
    else:
        if "hanime" in link_id:
            source = "hanime"
        elif "aniwatch" in link_id or "megaplay.buzz" in link_id or "1anime" in link_id:
            source = "aniwatch"
        elif "miruro" in link_id:
            source = "miruro"
        else:
            source = "animekai"
            
    if source == "hanime":
        res = resolve_hanime_source(link_id)
    elif source == "aniwatch":
        res = resolve_source(stripped_link)
    elif source == "miruro":
        res = resolve_source_miruro(stripped_link)
    else:
        res = resolve_source(stripped_link)
        
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]
        
    # Apply HLS Referrer Proxy to prevent CORS/referer blocks and avoid iframe falls
    if isinstance(res, dict) and "sources" in res:
        from urllib.parse import quote
        embed_url = res.get("embed_url") or res.get("embedUrl") or ""
        new_sources = []
        for s in res["sources"]:
            if isinstance(s, dict):
                s_copy = dict(s)
                file_url = s_copy.get("file", "")
                if s_copy.get("type") == "hls" or file_url.split("?")[0].endswith(".m3u8"):
                    cleaned_ref = get_base_origin(embed_url) if embed_url else ""
                    proxied = f"{request.host_url}api/proxy-hls/stream.m3u8?url={quote(file_url)}"
                    if cleaned_ref:
                        proxied += f"&referer={quote(cleaned_ref)}"
                    s_copy["file"] = proxied
                new_sources.append(s_copy)
        res["sources"] = new_sources

        # Strip CSP/X-Frame-Options by proxying player.hanime.tv on our own origin
        if link_id.startswith("hanime:") and new_sources:
            proxied_hls_url = new_sources[0]["file"]
            res["embed_url"] = f"{request.host_url}api/proxy-player#{quote(proxied_hls_url)}"

    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=180) # Cache video source for 3 minutes to keep URLs fresh
    return jsonify(final_res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
