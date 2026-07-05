import re
import requests
import uuid
from threading import Lock

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://anime.nexus",
    "Referer": "https://anime.nexus/",
}

PLAYWRIGHT_LOCK = Lock()
CF_COOKIES = []
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def map_search_item(show):
    if not show:
        return {}
    
    show_id = show.get("id")
    slug = show.get("slug")
    name = show.get("name")
    name_alt = show.get("name_alt") or name
    
    poster_path = None
    if show.get("poster") and show["poster"].get("resized"):
        poster_path = show["poster"]["resized"].get("640x960") or show["poster"]["resized"].get("480x720") or show["poster"]["resized"].get("240x360")
        
    release_date = show.get("release_date") or ""
    year = release_date[:4] if release_date else ""
    
    genres = [g.get("name") for g in show.get("genres", []) if isinstance(g, dict) and g.get("name")]
    
    return {
        "title": name,
        "japanese_title": name_alt,
        "slug": slug,
        "url": f"https://anime.nexus/series/{show_id}/{slug}",
        "poster": f"https://anime.delivery{poster_path}" if poster_path else "",
        "sub_episodes": str(show.get("episode_count") or 0),
        "dub_episodes": "",
        "total_episodes": str(show.get("episode_count") or 0),
        "year": year,
        "type": show.get("type") or "TV",
        "rating": show.get("parental_rating") or "PG-13",
        "genres": genres
    }

def map_latest_item(show):
    if not show:
        return {}
    
    show_id = show.get("id")
    slug = show.get("slug")
    name = show.get("name")
    name_alt = show.get("name_alt") or name
    
    poster_path = None
    if show.get("poster") and show["poster"].get("resized"):
        poster_path = show["poster"]["resized"].get("640x960") or show["poster"]["resized"].get("480x720") or show["poster"]["resized"].get("240x360")
        
    return {
        "title": name,
        "japanese_title": name_alt,
        "poster": f"https://anime.delivery{poster_path}" if poster_path else "",
        "url": f"https://anime.nexus/series/{show_id}/{slug}",
        "slug": slug,
        "current_episode": str(show.get("episode_count") or 0),
        "sub_episodes": str(show.get("episode_count") or 0),
        "dub_episodes": "",
        "type": show.get("type") or "TV"
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
        results = [map_search_item(show) for show in items]
        
        meta = data.get("meta", {})
        total = meta.get("total", len(results))
        
        return {
            "total": total,
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
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
            
        latest_mapped = [map_latest_item(show) for show in latest_items]
        
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
        return {"error": str(e)}, 500

def scrape_anime_info_animenexus(slug):
    try:
        url = "https://api.anime.nexus/api/anime/shows"
        target_id = None
        search_query = slug
        details_show_obj = None
        
        if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', slug, re.IGNORECASE):
            target_id = slug
            try:
                details_url = f"https://api.anime.nexus/api/anime/details?id={target_id}"
                r_det = requests.get(details_url, headers=HEADERS, timeout=10)
                if r_det.status_code == 200:
                    details_show_obj = r_det.json().get("data", {})
                    real_slug = details_show_obj.get("slug")
                    if real_slug:
                        search_query = real_slug
            except Exception as e:
                print(f"Failed to fetch details for UUID {target_id}: {e}")

        params = {
            "search": search_query,
            "includes[]": ["poster", "genres", "background"]
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        items = []
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", [])
            
        show = None
        if target_id:
            for item in items:
                if item.get("id") == target_id:
                    show = item
                    break
        else:
            for item in items:
                if item.get("slug") == slug:
                    show = item
                    break
                    
        if not show and items:
            show = items[0]
            
        if not show:
            if details_show_obj:
                show = details_show_obj
            else:
                return {"error": "Anime not found"}, 404
            
        show_id = show.get("id")
        
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
            
        poster_path = None
        if show.get("poster") and show["poster"].get("resized"):
            poster_path = show["poster"]["resized"].get("640x960") or show["poster"]["resized"].get("480x720")
        
        bg_path = None
        if show.get("background") and show["background"].get("resized"):
            bg_path = show["background"]["resized"].get("1920x1080") or show["background"]["resized"].get("1360x768")
            
        poster = f"https://anime.delivery{poster_path}" if poster_path else ""
        banner = f"https://anime.delivery{bg_path}" if bg_path else poster
            
        released = show.get("release_date") or "Unknown"
        status_map = {
            "Finished Airing": "Completed",
            "Currently Airing": "Ongoing",
            "Not Yet Aired": "Upcoming"
        }
        genres = [g.get("name") for g in show.get("genres", []) if isinstance(g, dict) and g.get("name")]
        
        detail = {
            "studio": "Unknown",
            "released": released,
            "views": "0",
            "likes": "0",
            "dislikes": "0",
            "downloads": "0",
            "genres": genres
        }
        
        return {
            "ani_id": str(show_id),
            "title": show.get("name"),
            "japanese_title": show.get("name_alt") or show.get("name"),
            "description": show.get("description") or "",
            "poster": poster,
            "banner": banner,
            "sub_episodes": str(sub_count),
            "dub_episodes": str(dub_count) if dub_count > 0 else "",
            "type": show.get("type") or "TV",
            "rating": show.get("parental_rating") or "PG-13",
            "mal_score": score,
            "detail": detail,
            "seasons": [],
        }
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes_animenexus(slug):
    try:
        url = "https://api.anime.nexus/api/anime/details/episodes"
        params = {
            "id": slug,
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
            
            token = f"animenexus:{slug}:{ep_id}:{ep_slug}"
            
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
        return {"error": str(e)}, 500

def refresh_cf_cookies(show_id, episode_id, episode_slug):
    if not sync_playwright:
        print("Playwright is not installed/available in this environment (running on serverless/cloud environment).")
        return False
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
                
            CF_COOKIES.clear()
            CF_COOKIES.extend(cookies)
            print(f"Successfully retrieved {len(CF_COOKIES)} cookies.")
            return True
        except Exception as e:
            print(f"Failed to retrieve cookies via Playwright: {e}")
            return False

def make_stream_request_via_playwright(show_id, episode_id, episode_slug):
    if not sync_playwright:
        print("Playwright is not installed/available in this environment.")
        return None
        
    with PLAYWRIGHT_LOCK:
        print("Capturing stream JSON using sync Playwright...")
        try:
            show_slug = ""
            try:
                url = f"https://api.anime.nexus/api/anime/shows/{show_id}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    show_slug = r.json().get("data", {}).get("slug", "")
            except Exception as e:
                print(f"Failed to fetch show slug for navigation: {e}")

            captured_json = None

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=CF_USER_AGENT,
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()
                
                def handle_response(response):
                    nonlocal captured_json
                    url = response.url
                    if "details/episode/stream" in url and response.status == 200:
                        try:
                            captured_json = response.json()
                            print("Captured stream JSON successfully!")
                        except Exception as e:
                            print(f"Error parsing captured JSON: {e}")

                page.on("response", handle_response)
                
                if show_slug:
                    series_url = f"https://anime.nexus/series/{show_id}/{show_slug}"
                    print(f"Playwright navigating to series: {series_url}")
                    page.goto(series_url, timeout=30000)
                    page.wait_for_timeout(3000)
                else:
                    print("Playwright navigating to home page fallback")
                    page.goto("https://anime.nexus/", timeout=30000)
                    page.wait_for_timeout(3000)

                watch_url = f"https://anime.nexus/watch/{episode_id}/{episode_slug}"
                print(f"Playwright navigating to watch: {watch_url}")
                page.goto(watch_url, timeout=30000)
                
                for _ in range(15):
                    if captured_json is not None:
                        break
                    page.wait_for_timeout(1000)
                
                browser.close()
                
            return captured_json
        except Exception as e:
            print(f"Failed to capture stream via Playwright: {e}")
            return None

def resolve_animenexus_source(link_id):
    try:
        parts = link_id.split(":")
        if len(parts) < 4:
            return {"error": "Invalid link_id format"}, 400
            
        show_id = parts[1]
        episode_id = parts[2]
        episode_slug = parts[3]
        
        watch_url = f"https://anime.nexus/watch/{episode_id}/{episode_slug}"
        
        data = make_stream_request_via_playwright(show_id, episode_id, episode_slug)
        if not data:
            return {
                "embed_url": watch_url,
                "skip": {},
                "sources": [],
                "tracks": [],
                "download": ""
            }

        stream_data = data.get("data", {})
        hls_url = stream_data.get("url")
        if not hls_url:
            return {"error": "No stream URL found in the intercepted data"}, 404

        video_meta = stream_data.get("video_meta") or {}
        subtitles = video_meta.get("subtitles") or []
        
        tracks = []
        for sub in subtitles:
            language = sub.get("language", "English")
            sub_url = sub.get("url")
            if sub_url:
                tracks.append({
                    "file": f"https://api.anime.nexus{sub_url}",
                    "label": language,
                    "kind": "captions",
                    "default": language.lower() == "english"
                })

        return {
            "embed_url": watch_url,
            "skip": {},
            "sources": [{"file": hls_url, "type": "hls", "label": "Auto"}],
            "tracks": tracks,
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
