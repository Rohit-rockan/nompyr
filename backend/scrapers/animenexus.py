import re
import requests
import uuid
from threading import Lock
from playwright.sync_api import sync_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://anime.nexus",
    "Referer": "https://anime.nexus/",
}

PLAYWRIGHT_LOCK = Lock()
CF_COOKIES = []
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def map_animenexus_item(show):
    if not show:
        return {}
    
    show_id = show.get("id")
    slug = show.get("slug")
    name = show.get("name")
    name_alt = show.get("name_alt") or name
    
    poster_path = None
    if show.get("poster") and show["poster"].get("resized"):
        poster_path = show["poster"]["resized"].get("640x960") or show["poster"]["resized"].get("480x720") or show["poster"]["resized"].get("240x360")
        
    bg_path = None
    if show.get("background") and show["background"].get("resized"):
        bg_path = show["background"]["resized"].get("1920x1080") or show["background"]["resized"].get("1360x768") or show["background"]["resized"].get("960x540")
        
    release_date = show.get("release_date") or ""
    year = release_date[:4] if release_date else ""
    
    genres = [g.get("name") for g in show.get("genres", []) if isinstance(g, dict) and g.get("name")]
    
    status_map = {
        "Finished Airing": "Completed",
        "Currently Airing": "Ongoing",
        "Not Yet Aired": "Upcoming"
    }
    status = status_map.get(show.get("status"), "Completed")
    
    return {
        "id": f"animenexus:{show_id}",
        "ani_id": f"animenexus:{show_id}",
        "slug": slug,
        "title": name,
        "japanese_title": name_alt,
        "poster": f"https://anime.delivery{poster_path}" if poster_path else "",
        "banner": f"https://anime.delivery{bg_path}" if bg_path else (f"https://anime.delivery{poster_path}" if poster_path else ""),
        "type": show.get("type") or "TV",
        "status": status,
        "year": year,
        "season": "TBA",
        "rating": show.get("parental_rating") or "PG-13",
        "score": "N/A",
        "duration": "24m",
        "studio": "Unknown",
        "genres": genres,
        "sub_episodes": str(show.get("episode_count") or 0),
        "dub_episodes": "",
        "total_episodes": str(show.get("episode_count") or 0),
        "current_episode": str(show.get("episode_count") or 0),
        "description": show.get("description") or "",
        "url": f"https://anime.nexus/series/{show_id}/{slug}"
    }

def search_anime_animenexus(keyword, page=1):
    try:
        url = "https://api.anime.nexus/api/anime/shows"
        params = {
            "search": keyword,
            "sortBy": "name asc",
            "hasVideos": "true",
            "page": page,
            "includes[]": ["poster", "genres"]
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {"error": f"Failed to search: {r.status_code}"}, r.status_code
            
        data = r.json()
        items = data.get("data", [])
        results = [map_animenexus_item(show) for show in items]
        
        meta = data.get("meta", {})
        total = meta.get("total", len(results))
        
        return {
            "total": total,
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        print(f"Error searching Anime Nexus: {e}")
        return {"error": str(e)}, 500

def scrape_home_animenexus():
    try:
        url = "https://api.anime.nexus/api/anime/shows"
        params_banner = {
            "sortBy": "release_date desc",
            "hasVideos": "true",
            "page": 1,
            "includes[]": ["poster", "genres", "background"]
        }
        r_banner = requests.get(url, params=params_banner, headers=HEADERS, timeout=10)
        
        params_latest = {
            "sortBy": "created_at desc",
            "hasVideos": "true",
            "page": 1,
            "includes[]": ["poster", "genres"]
        }
        r_latest = requests.get(url, params=params_latest, headers=HEADERS, timeout=10)
        
        banner_items = r_banner.json().get("data", []) if r_banner.status_code == 200 else []
        latest_items = r_latest.json().get("data", []) if r_latest.status_code == 200 else []
        
        banner_mapped = []
        for show in banner_items[:5]:
            bg_path = None
            if show.get("background") and show["background"].get("resized"):
                bg_path = show["background"]["resized"].get("1920x1080") or show["background"]["resized"].get("1360x768")
            poster_path = None
            if show.get("poster") and show["poster"].get("resized"):
                poster_path = show["poster"]["resized"].get("640x960") or show["poster"]["resized"].get("480x720")
            
            desc = show.get("description") or ""
            desc = re.sub('<[^<]+?>', '', desc).strip()
            if len(desc) > 200:
                desc = desc[:200] + "..."
                
            banner_mapped.append({
                "title": show.get("name"),
                "japanese_title": show.get("name_alt") or show.get("name"),
                "description": desc,
                "poster": f"https://anime.delivery{poster_path}" if poster_path else "",
                "url": f"https://anime.nexus/series/{show.get('id')}/{show.get('slug')}",
                "slug": show.get("slug"),
                "sub_episodes": str(show.get("episode_count") or 0),
                "dub_episodes": "",
                "type": show.get("type") or "TV",
                "genres": ", ".join([g.get("name") for g in show.get("genres", []) if isinstance(g, dict) and g.get("name")]),
                "rating": show.get("parental_rating") or "PG-13",
                "release": show.get("release_date")[:4] if show.get("release_date") else "",
                "quality": "HD"
            })
            
        latest_mapped = [map_animenexus_item(show) for show in latest_items]
        
        trending_list = latest_mapped[:15]
        trending = {
            "NOW": trending_list,
            "DAY": trending_list,
            "WEEK": trending_list,
            "MONTH": trending_list
        }
        
        return {
            "banner": banner_mapped,
            "latest_updates": latest_mapped[:24],
            "top_trending": trending,
            "popular": latest_mapped[:24],
            "upcoming": latest_mapped[:24]
        }
    except Exception as e:
        print(f"Error scraping Anime Nexus home: {e}")
        return {"error": str(e)}, 500

def scrape_anime_info_animenexus(slug):
    try:
        url = "https://api.anime.nexus/api/anime/shows"
        params = {
            "search": slug,
            "includes[]": ["poster", "genres", "background"]
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {"error": f"Failed to fetch show details: {r.status_code}"}, r.status_code
            
        data = r.json()
        items = data.get("data", [])
        
        # Find exact match by slug
        show = None
        for item in items:
            if item.get("slug") == slug:
                show = item
                break
        if not show and items:
            show = items[0]
            
        if not show:
            return {"error": "Anime not found"}, 404
            
        show_id = show.get("id")
        
        mapped = map_animenexus_item(show)
        
        score = "N/A"
        try:
            stats_url = f"https://api.anime.nexus/api/anime/details/statistics?id={show_id}"
            r_stats = requests.get(stats_url, headers=HEADERS, timeout=5)
            if r_stats.status_code == 200:
                stats_data = r_stats.json()
                score_val = stats_data.get("rating") or stats_data.get("score")
                if score_val:
                    score = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else str(score_val)
        except Exception as e:
            print(f"Failed to fetch statistics: {e}")
            
        mapped["score"] = score
        
        sub_count = 0
        dub_count = 0
        try:
            eps_data = fetch_episodes_animenexus(show_id)
            if isinstance(eps_data, list):
                sub_count = len(eps_data)
                dub_count = sum(1 for ep in eps_data if ep.get("has_dub"))
        except Exception as e:
            print(f"Failed to fetch episodes count for details: {e}")
            
        if sub_count == 0:
            sub_count = show.get("episode_count") or 1
            
        mapped["sub_episodes"] = str(sub_count)
        mapped["dub_episodes"] = str(dub_count) if dub_count > 0 else ""
        
        released = show.get("release_date") or "Unknown"
        detail = {
            "released": released,
            "rating": mapped["rating"],
            "score": score,
            "genres": mapped["genres"],
            "status": mapped["status"]
        }
        
        return {
            "ani_id": f"animenexus:{show_id}",
            "title": mapped["title"],
            "japanese_title": mapped["japanese_title"],
            "description": mapped["description"],
            "poster": mapped["poster"],
            "banner": mapped["banner"],
            "sub_episodes": str(sub_count),
            "dub_episodes": str(dub_count) if dub_count > 0 else "",
            "type": mapped["type"],
            "rating": mapped["rating"],
            "mal_score": score,
            "detail": detail,
            "seasons": [],
        }
    except Exception as e:
        print(f"Error scraping Anime Nexus info: {e}")
        return {"error": str(e)}, 500

def fetch_episodes_animenexus(show_id):
    try:
        url = "https://api.anime.nexus/api/anime/details/episodes"
        params = {
            "id": show_id,
            "page": 1,
            "perPage": 500,
            "order": "asc",
            "fillers": "true",
            "recaps": "true"
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {"error": f"Failed to fetch episodes: {r.status_code}"}, r.status_code
            
        data = r.json()
        eps = data.get("data", [])
        
        episode_list = []
        for ep in eps:
            num = ep.get("number")
            if num is None:
                continue
            num_str = str(num)
            
            ep_id = ep.get("id")
            ep_slug = ep.get("slug") or f"episode-{num_str}"
            title = ep.get("title") or f"Episode {num_str}"
            
            video_meta = ep.get("video_meta") or {}
            audio_langs = [a.lower() for a in video_meta.get("audio_languages", [])]
            
            has_sub = True
            has_dub = any("eng" in a or "english" in a for a in audio_langs)
            
            token = f"animenexus:{show_id}:{ep_id}:{ep_slug}"
            
            episode_list.append({
                "number": num_str,
                "slug": ep_slug,
                "title": title,
                "japanese_title": "",
                "token": token,
                "has_sub": has_sub,
                "has_dub": has_dub
            })
            
        return episode_list
    except Exception as e:
        print(f"Error fetching Anime Nexus episodes: {e}")
        return {"error": str(e)}, 500

def fetch_servers_animenexus(ep_token):
    try:
        parts = ep_token.split(":")
        if len(parts) < 4:
            return {"error": "Invalid ep_token format"}, 400
            
        show_id = parts[1]
        ep_id = parts[2]
        ep_slug = parts[3]
        
        url = "https://api.anime.nexus/api/anime/details/episodes"
        params = {
            "id": show_id,
            "page": 1,
            "perPage": 500,
            "order": "asc",
            "fillers": "true",
            "recaps": "true"
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        has_sub = True
        has_dub = False
        if r.status_code == 200:
            eps = r.json().get("data", [])
            for ep in eps:
                if ep.get("id") == ep_id:
                    video_meta = ep.get("video_meta") or {}
                    audio_langs = [a.lower() for a in video_meta.get("audio_languages", [])]
                    has_dub = any("eng" in a or "english" in a for a in audio_langs)
                    break
                    
        sub_servers = []
        dub_servers = []
        
        if has_sub:
            sub_servers.append({
                "name": "Anime Nexus",
                "server_id": "animenexus-direct-sub",
                "episode_id": ep_id,
                "link_id": f"animenexus:{show_id}:{ep_id}:{ep_slug}:sub"
            })
        if has_dub:
            dub_servers.append({
                "name": "Anime Nexus",
                "server_id": "animenexus-direct-dub",
                "episode_id": ep_id,
                "link_id": f"animenexus:{show_id}:{ep_id}:{ep_slug}:dub"
            })
            
        return {
            "watching": "Anime Nexus Player",
            "servers": {
                "sub": sub_servers,
                "dub": dub_servers
            }
        }
    except Exception as e:
        print(f"Error fetching servers for Anime Nexus: {e}")
        return {"error": str(e)}, 500

def refresh_cf_cookies(show_id, episode_id, episode_slug):
    global CF_COOKIES
    with PLAYWRIGHT_LOCK:
        print("Refreshing Cloudflare cookies using sync Playwright...")
        try:
            show_slug = ""
            try:
                url = f"https://api.anime.nexus/api/anime/shows/{show_id}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    show_slug = r.json().get("data", {}).get("slug", "")
            except Exception as e:
                print(f"Failed to fetch show slug for navigation: {e}")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=CF_USER_AGENT,
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()
                
                if show_slug:
                    series_url = f"https://anime.nexus/series/{show_id}/{show_slug}"
                    print(f"Playwright navigating to series: {series_url}")
                    page.goto(series_url, timeout=30000)
                    page.wait_for_timeout(5000)
                else:
                    print("Playwright navigating to home page fallback")
                    page.goto("https://anime.nexus/", timeout=30000)
                    page.wait_for_timeout(5000)

                watch_url = f"https://anime.nexus/watch/{episode_id}/{episode_slug}"
                print(f"Playwright navigating to watch: {watch_url}")
                page.goto(watch_url, timeout=30000)
                page.wait_for_timeout(8000)
                
                cookies = context.cookies()
                browser.close()
                
            CF_COOKIES = cookies
            print(f"Successfully retrieved {len(CF_COOKIES)} cookies.")
            return True
        except Exception as e:
            print(f"Failed to retrieve cookies via Playwright: {e}")
            return False

def make_stream_request(episode_id):
    url = f"https://api.anime.nexus/api/anime/details/episode/stream?id={episode_id}&fillers=true&recaps=true"
    session = requests.Session()
    if CF_COOKIES:
        for c in CF_COOKIES:
            session.cookies.set(c["name"], c["value"], domain=c["domain"])
            
    fingerprint = str(uuid.uuid4())
    headers = {
        "User-Agent": CF_USER_AGENT,
        "Origin": "https://anime.nexus",
        "Referer": "https://anime.nexus/",
        "Accept": "application/json, text/plain, */*",
        "x-client-fingerprint": fingerprint,
        "x-fingerprint": fingerprint
    }
    
    r = session.get(url, headers=headers, timeout=15)
    return r

def resolve_source_animenexus(link_id):
    try:
        parts = link_id.split(":")
        if len(parts) < 4:
            return {"error": "Invalid link_id format"}, 400
            
        show_id = parts[0]
        episode_id = parts[1]
        episode_slug = parts[2]
        lang = parts[3]
        
        r = make_stream_request(episode_id)
        if r.status_code == 403 or r.status_code == 401 or not CF_COOKIES:
            print("Direct request failed (403/401) or no cookies cached. Refreshing cookies...")
            if refresh_cf_cookies(show_id, episode_id, episode_slug):
                r = make_stream_request(episode_id)
                
        if r.status_code != 200:
            return {"error": f"Failed to fetch stream details: {r.status_code}", "text": r.text}, r.status_code
            
        stream_data = r.json().get("data", {})
        hls_url = stream_data.get("hls")
        if not hls_url:
            return {"error": "HLS URL not found in stream data"}, 404
            
        subtitles = stream_data.get("subtitles", [])
        tracks = []
        for sub in subtitles:
            tracks.append({
                "file": sub.get("src"),
                "label": sub.get("label", "Unknown"),
                "kind": "captions",
                "default": sub.get("label", "").lower() == "english"
            })
            
        sources = [
            {
                "file": hls_url,
                "type": "hls",
                "label": "Auto"
            }
        ]
        
        return {
            "embed_url": "https://anime.nexus/",
            "skip": {
                "intro": [0, 0],
                "outro": [0, 0]
            },
            "sources": sources,
            "tracks": tracks,
            "download": ""
        }
    except Exception as e:
        print(f"Error resolving source for Anime Nexus: {e}")
        return {"error": str(e)}, 500
