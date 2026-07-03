import re
import json as _json
import base64
import gzip
import requests

MIRURO_PIPE_URL = "https://www.miruro.bz/api/secure/pipe"
MIRURO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.miruro.bz/"
}
ANILIST_URL = "https://graphql.anilist.co"

def _translate_id(encoded_id: str) -> str:
    try:
        decoded = base64.urlsafe_b64decode(encoded_id + '=' * (4 - len(encoded_id) % 4)).decode()
        if ':' in decoded:
            return decoded
        return encoded_id
    except Exception as e:
        return {"error": str(e)}, 500

def _deep_translate(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'id' and isinstance(value, str):
                obj[key] = _translate_id(value)
            elif isinstance(value, (dict, list)):
                _deep_translate(value)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                _deep_translate(item)

def _encode_pipe_request(payload: dict) -> str:
    return base64.urlsafe_b64encode(_json.dumps(payload).encode()).decode().rstrip('=')

def _decode_pipe_response(encoded_str: str) -> dict:
    try:
        encoded_str += '=' * (4 - len(encoded_str) % 4)
        compressed = base64.urlsafe_b64decode(encoded_str)
        return _json.loads(gzip.decompress(compressed).decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}, 500

def _anilist_query(query: str, variables: dict = None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    res = requests.post(ANILIST_URL, json=body, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15.0)
    if res.status_code != 200:
        raise Exception(f"AniList query failed with status {res.status_code}")
    return res.json().get("data", {})

MEDIA_LIST_FIELDS = """
    id
    title { romaji english native }
    coverImage { large extraLarge }
    bannerImage
    format
    season
    seasonYear
    episodes
    duration
    status
    averageScore
    meanScore
    popularity
    favourites
    genres
    source
    countryOfOrigin
    isAdult
    studios(isMain: true) { nodes { name isAnimationStudio } }
    nextAiringEpisode { episode airingAt timeUntilAiring }
    startDate { year month day }
    endDate { year month day }
"""

def map_search_item(media):
    if not media:
        return {}
    anilist_id = media.get("id")
    title_data = media.get("title") or {}
    title = title_data.get("english") or title_data.get("romaji") or title_data.get("native") or "Untitled"
    jp_title = title_data.get("romaji") or title_data.get("native") or title
    
    cover_image = media.get("coverImage") or {}
    poster = cover_image.get("extraLarge") or cover_image.get("large") or ""
    
    episodes_count = media.get("episodes") or 1
        
    return {
        "title": title,
        "japanese_title": jp_title,
        "slug": str(anilist_id),
        "url": f"/anime/miruro/{anilist_id}",
        "poster": poster,
        "sub_episodes": str(episodes_count),
        "dub_episodes": "",
        "total_episodes": str(episodes_count),
        "year": str(media.get("seasonYear") or ""),
        "type": media.get("format") or "TV",
        "rating": "PG-13" if not media.get("isAdult") else "R+",
        "genres": media.get("genres") or []
    }

def map_latest_item(media):
    if not media:
        return {}
    anilist_id = media.get("id")
    title_data = media.get("title") or {}
    title = title_data.get("english") or title_data.get("romaji") or title_data.get("native") or "Untitled"
    jp_title = title_data.get("romaji") or title_data.get("native") or title
    
    cover_image = media.get("coverImage") or {}
    poster = cover_image.get("extraLarge") or cover_image.get("large") or ""
    
    episodes_count = media.get("episodes") or 1
        
    return {
        "title": title,
        "japanese_title": jp_title,
        "poster": poster,
        "url": f"/anime/miruro/{anilist_id}",
        "slug": str(anilist_id),
        "current_episode": str(episodes_count),
        "sub_episodes": str(episodes_count),
        "dub_episodes": "",
        "type": media.get("format") or "TV"
    }

def search_anime_miruro(keyword, page=1):
    try:
        gql = f"""
        query ($search: String, $page: Int, $perPage: Int) {{
            Page(page: $page, perPage: $perPage) {{
                pageInfo {{ total currentPage lastPage hasNextPage perPage }}
                media(search: $search, type: ANIME, sort: SEARCH_MATCH) {{
                    {MEDIA_LIST_FIELDS}
                }}
            }}
        }}
        """
        data = _anilist_query(gql, {"search": keyword, "page": page, "perPage": 24})
        page_data = data.get("Page", {})
        page_info = page_data.get("pageInfo", {})
        results = [map_search_item(m) for m in page_data.get("media", [])]
        
        return {
            "total": page_info.get("total", len(results)),
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_home_miruro():
    try:
        gql = f"""
        query {{
            trending: Page(page: 1, perPage: 24) {{
                media(type: ANIME, sort: [TRENDING_DESC, POPULARITY_DESC]) {{
                    {MEDIA_LIST_FIELDS}
                    description(asHtml: false)
                }}
            }}
            popular: Page(page: 1, perPage: 24) {{
                media(type: ANIME, sort: [POPULARITY_DESC]) {{
                    {MEDIA_LIST_FIELDS}
                }}
            }}
            latest: Page(page: 1, perPage: 24) {{
                media(type: ANIME, sort: [START_DATE_DESC], status: RELEASING) {{
                    {MEDIA_LIST_FIELDS}
                }}
            }}
            upcoming: Page(page: 1, perPage: 24) {{
                media(type: ANIME, sort: [POPULARITY_DESC], status: NOT_YET_RELEASED) {{
                    {MEDIA_LIST_FIELDS}
                }}
            }}
        }}
        """
        data = _anilist_query(gql)
        
        trending_raw = data.get("trending", {}).get("media", [])
        popular_raw = data.get("popular", {}).get("media", [])
        latest_raw = data.get("latest", {}).get("media", [])
        upcoming_raw = data.get("upcoming", {}).get("media", [])
        
        trending_mapped = [map_latest_item(m) for m in trending_raw]
        popular_mapped = [map_latest_item(m) for m in popular_raw]
        latest_mapped = [map_latest_item(m) for m in latest_raw]
        upcoming_mapped = [map_latest_item(m) for m in upcoming_raw]
        
        banner = []
        for m in trending_raw[:5]:
            mapped = map_latest_item(m)
            desc = m.get("description") or ""
            if desc:
                desc = re.sub('<[^<]+?>', '', desc).strip()
                if len(desc) > 200:
                    desc = desc[:200] + "..."
            
            genres = m.get("genres") or []
            year = str(m.get("seasonYear") or "")
            rating = "PG-13" if not m.get("isAdult") else "R+"
            banner.append({
                "title": mapped["title"],
                "japanese_title": mapped["japanese_title"],
                "description": desc,
                "poster": mapped["poster"],
                "url": mapped["url"],
                "slug": mapped["slug"],
                "sub_episodes": mapped["sub_episodes"],
                "dub_episodes": "",
                "type": mapped["type"],
                "genres": ", ".join(genres),
                "rating": rating,
                "release": year,
                "quality": "HD"
            })
            
        trending = {
            "NOW": trending_mapped[:15],
            "DAY": trending_mapped[:15],
            "WEEK": trending_mapped[:15],
            "MONTH": trending_mapped[:15]
        }
        
        return {
            "banner": banner,
            "latest_updates": latest_mapped,
            "top_trending": trending,
            "popular": popular_mapped,
            "upcoming": upcoming_mapped
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_miruro(slug):
    try:
        anilist_id = int(slug)
    except ValueError:
        return {"error": "Invalid AniList ID"}, 400
        
    gql = """
    query ($id: Int) {
        Media(id: $id, type: ANIME) {
            id
            title { romaji english native }
            description(asHtml: false)
            coverImage { large extraLarge color }
            bannerImage
            format
            season
            seasonYear
            episodes
            duration
            status
            averageScore
            genres
            isAdult
            studios(isMain: true) { nodes { name isAnimationStudio } }
            startDate { year month day }
        }
    }
    """
    try:
        data = _anilist_query(gql, {"id": anilist_id})
        media = data.get("Media")
        if not media:
            return {"error": "Anime not found"}, 404
            
        title_data = media.get("title") or {}
        title = title_data.get("english") or title_data.get("romaji") or title_data.get("native") or "Untitled"
        jp_title = title_data.get("romaji") or title_data.get("native") or title
        
        cover_image = media.get("coverImage") or {}
        poster = cover_image.get("extraLarge") or cover_image.get("large") or ""
        banner = media.get("bannerImage") or poster
        
        studios_nodes = media.get("studios", {}).get("nodes", []) if media.get("studios") else []
        studio = next((s.get("name") for s in studios_nodes if s.get("isAnimationStudio")), None) or (studios_nodes[0].get("name") if studios_nodes else "Unknown")
        
        start_date = media.get("startDate") or {}
        released = f"{start_date.get('year', 'Unknown')}-{start_date.get('month', 'Unknown')}-{start_date.get('day', 'Unknown')}"
        
        status_map = {
            "FINISHED": "Completed",
            "RELEASING": "Ongoing",
            "NOT_YET_RELEASED": "Upcoming",
            "CANCELLED": "Cancelled",
            "HIATUS": "Hiatus"
        }
        status = status_map.get(media.get("status"), "Unknown")
        
        score = media.get("averageScore")
        if score is not None:
            score = f"{score / 10:.1f}"
        else:
            score = "N/A"
            
        sub_count = 0
        dub_count = 0
        try:
            ep_data = _fetch_raw_episodes_miruro(anilist_id)
            providers = ep_data.get("providers", {})
            for prov_name, prov_data in providers.items():
                if not isinstance(prov_data, dict):
                    continue
                episodes = prov_data.get("episodes", {})
                if isinstance(episodes, list):
                    episodes = {"sub": episodes}
                if isinstance(episodes, dict):
                    sub_count = max(sub_count, len(episodes.get("sub", [])))
                    dub_count = max(dub_count, len(episodes.get("dub", [])))
        except Exception as e:
            print(f"Error fetching episodes for count in info: {e}")
            
        if sub_count == 0:
            sub_count = media.get("episodes") or 1

        detail = {
            "studio": studio,
            "released": released,
            "views": "0",
            "likes": "0",
            "dislikes": "0",
            "downloads": "0",
            "genres": media.get("genres") or []
        }
        
        return {
            "ani_id": str(anilist_id),
            "title": title,
            "japanese_title": jp_title,
            "description": media.get("description") or "",
            "poster": poster,
            "banner": banner,
            "sub_episodes": str(sub_count),
            "dub_episodes": str(dub_count) if dub_count > 0 else "",
            "type": media.get("format") or "TV",
            "rating": "PG-13" if not media.get("isAdult") else "R+",
            "mal_score": score,
            "detail": detail,
            "seasons": [],
        }
    except Exception as e:
        return {"error": str(e)}, 500

def _fetch_raw_episodes_miruro(anilist_id):
    payload = {
        "path": "episodes",
        "method": "GET",
        "query": {"anilistId": anilist_id},
        "body": None,
        "version": "0.1.0",
    }
    encoded_req = _encode_pipe_request(payload)
    r = requests.get(f"{MIRURO_PIPE_URL}?e={encoded_req}", headers=MIRURO_HEADERS, timeout=15.0)
    if r.status_code != 200:
        raise Exception(f"Miruro pipe episodes request failed with status {r.status_code}")
    
    encoded_str = r.text.strip()
    data = _decode_pipe_response(encoded_str)
    _deep_translate(data)
    return data

def fetch_episodes_miruro(slug):
    try:
        anilist_id = int(slug)
    except ValueError:
        return []
        
    try:
        data = _fetch_raw_episodes_miruro(anilist_id)
        providers = data.get("providers", {})
        
        episode_map = {}
        for prov_name, prov_data in providers.items():
            if not isinstance(prov_data, dict):
                continue
            episodes = prov_data.get("episodes", {})
            if isinstance(episodes, list):
                episodes = {"sub": episodes}
            if not isinstance(episodes, dict):
                continue
                
            for cat, ep_list in episodes.items():
                if not isinstance(ep_list, list):
                    continue
                for ep in ep_list:
                    if not isinstance(ep, dict):
                        continue
                    num = ep.get("number")
                    if num is None:
                        continue
                    try:
                        num_f = float(num)
                        num_str = str(int(num_f)) if num_f.is_integer() else str(num_f)
                    except ValueError:
                        num_str = str(num)
                        
                    title = ep.get("title") or f"Episode {num_str}"
                    
                    if num_str not in episode_map:
                        episode_map[num_str] = {
                            "number": num_str,
                            "slug": f"ep-{num_str}",
                            "title": title,
                            "japanese_title": "",
                            "token": f"miruro:{anilist_id}:{num_str}",
                            "has_sub": False,
                            "has_dub": False
                        }
                    if cat == "sub":
                        episode_map[num_str]["has_sub"] = True
                    elif cat == "dub":
                        episode_map[num_str]["has_dub"] = True
                        
        sorted_keys = sorted(episode_map.keys(), key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else 9999)
        return [episode_map[k] for k in sorted_keys]
    except Exception as e:
        return []

def fetch_servers_miruro(ep_token):
    try:
        parts = ep_token.split(":")
        if len(parts) >= 3:
            anilist_id = int(parts[1])
            ep_num = parts[2]
        else:
            return {"error": "Invalid ep_token format"}, 400
    except ValueError:
        return {"error": "Invalid token"}, 400
        
    try:
        data = _fetch_raw_episodes_miruro(anilist_id)
        providers = data.get("providers", {})
        
        sub_servers = []
        dub_servers = []
        
        for prov_name, prov_data in providers.items():
            if not isinstance(prov_data, dict):
                continue
            episodes = prov_data.get("episodes", {})
            if isinstance(episodes, list):
                episodes = {"sub": episodes}
            if not isinstance(episodes, dict):
                continue
                
            for cat, ep_list in episodes.items():
                if not isinstance(ep_list, list):
                    continue
                for ep in ep_list:
                    if not isinstance(ep, dict):
                        continue
                    num = ep.get("number")
                    if num is None:
                        continue
                    try:
                        num_f = float(num)
                        num_str = str(int(num_f)) if num_f.is_integer() else str(num_f)
                    except ValueError:
                        num_str = str(num)
                        
                    if num_str == ep_num:
                        orig_id = ep.get("id")
                        if not orig_id:
                            continue
                            
                        link_id = f"miruro_server:{prov_name}:{cat}:{anilist_id}:{ep_num}:{orig_id}"
                        
                        server_info = {
                            "name": f"{prov_name.capitalize()} ({cat.capitalize()})",
                            "server_id": f"miruro-{prov_name}-{cat}",
                            "episode_id": ep_num,
                            "link_id": link_id
                        }
                        if cat == "sub":
                            sub_servers.append(server_info)
                        else:
                            dub_servers.append(server_info)
                            
        return {
            "watching": "Miruro Player",
            "servers": {
                "sub": sub_servers,
                "dub": dub_servers
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_miruro_source(link_id):
    try:
        if not link_id.startswith("miruro_server:"):
            return {"error": "Invalid link_id format"}, 400
        
        parts = link_id.split(":")
        if len(parts) < 6:
            return {"error": "Invalid link_id format"}, 400
            
        provider = parts[1]
        category = parts[2]
        anilist_id = parts[3]
        ep_num = parts[4]
        orig_id = parts[5]
        
        watch_url = f"https://www.miruro.tv/watch?id={anilist_id}&ep={ep_num}"
        
        try:
            enc_id = base64.urlsafe_b64encode(orig_id.encode()).decode().rstrip('=')
            payload = {
                "path": "sources",
                "method": "GET",
                "query": {
                    "episodeId": enc_id,
                    "provider": provider,
                    "category": category,
                    "anilistId": int(anilist_id),
                },
                "body": None,
                "version": "0.1.0",
            }
            encoded_req = _encode_pipe_request(payload)
            res = requests.get(f"{MIRURO_PIPE_URL}?e={encoded_req}", headers=MIRURO_HEADERS, timeout=15)
            
            if res.status_code == 200:
                data = _decode_pipe_response(res.text.strip())
                _deep_translate(data)
                
                streams = data.get("streams", [])
                if streams:
                    stream = streams[0]
                    stream_url = stream.get("url")
                    
                    subtitles = data.get("subtitles") or []
                    tracks = []
                    for sub in subtitles:
                        label = sub.get("label", "English")
                        sub_url = sub.get("file") or sub.get("url")
                        if sub_url:
                            tracks.append({
                                "file": sub_url,
                                "label": label,
                                "kind": "captions",
                                "default": label.lower() == "english"
                            })
                            
                    return {
                        "embed_url": "https://bysekoze.com/",
                        "skip": {},
                        "sources": [{"file": stream_url, "type": "mp4", "label": "Auto"}],
                        "tracks": tracks,
                        "download": ""
                    }
        except Exception as api_err:
            pass

        return {
            "embed_url": watch_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
