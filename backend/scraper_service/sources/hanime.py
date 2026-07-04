import re
import json as _json
import requests

HANIME_API_BASE = "https://hanime.tv/api/v8"
HANIME_SEARCH_URL = "https://search.htv-services.com/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://hanime.tv/",
}

def scrape_home_hanime():
    try:
        url = f"{HANIME_API_BASE}/landing"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        sections = data.get("sections", [])
        
        video_map = {}
        for v in data.get("hentai_videos", []):
            v_id = v.get("id")
            if v_id:
                video_map[v_id] = v
                    
        def map_video_list(id_list):
            result_list = []
            for v_id in id_list:
                v = video_map.get(v_id)
                if not v: continue
                cover = v.get("cover_url") or ""
                poster = cover.replace("/covers/", "/posters/") if "/covers/" in cover else cover
                result_list.append({
                    "title": v.get("name", ""),
                    "japanese_title": "",
                    "poster": poster,
                    "url": f"https://hanime.tv/videos/hentai/{v.get('slug', '')}",
                    "slug": v.get("slug", ""),
                    "current_episode": "1",
                    "sub_episodes": "1",
                    "dub_episodes": "",
                    "type": "OVA",
                })
            return result_list
            
        latest = []
        trending_list = []
        popular = []
        upcoming = []
        
        for s in sections:
            title = s.get("title", "").lower()
            ids = s.get("hentai_video_ids", [])
            if "recent" in title:
                latest = map_video_list(ids)
            elif "trending" in title:
                trending_list = map_video_list(ids)
            elif "new" in title:
                popular = map_video_list(ids)
            elif "random" in title:
                upcoming = map_video_list(ids)
                
        all_videos = list(video_map.values())
        fallback_list = []
        for v in all_videos[:24]:
            cover = v.get("cover_url") or ""
            poster = cover.replace("/covers/", "/posters/") if "/covers/" in cover else cover
            fallback_list.append({
                "title": v.get("name", ""),
                "japanese_title": "",
                "poster": poster,
                "url": f"https://hanime.tv/videos/hentai/{v.get('slug', '')}",
                "slug": v.get("slug", ""),
                "current_episode": "1",
                "sub_episodes": "1",
                "dub_episodes": "",
                "type": "OVA",
            })
            
        if not latest: latest = fallback_list
        if not trending_list: trending_list = fallback_list
        if not popular: popular = fallback_list
        if not upcoming: upcoming = fallback_list
        
        banner = []
        for item in trending_list[:5]:
            banner.append({
                "title": item["title"],
                "japanese_title": "",
                "description": "Watch " + item["title"] + " on HAnime.tv.",
                "poster": item["poster"],
                "url": item["url"],
                "slug": item["slug"],
                "sub_episodes": "1",
                "dub_episodes": "",
                "type": "OVA",
                "genres": "",
                "rating": "18+",
                "release": "",
                "quality": "HD",
            })
            
        trending = {
            "NOW": trending_list,
            "DAY": trending_list,
            "WEEK": trending_list,
            "MONTH": trending_list
        }
        
        return {
            "banner": banner,
            "latest_updates": latest,
            "top_trending": trending,
            "popular": popular,
            "upcoming": upcoming
        }
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_hanime(keyword, page=1):
    try:
        api_page = page - 1 if page > 1 else 0
        payload = {
            "search_text": keyword,
            "tags": [],
            "brands": [],
            "blacklist": [],
            "order_by": "created_at_unix",
            "ordering": "desc",
            "page": api_page
        }
        
        response = requests.post(HANIME_SEARCH_URL, headers=HEADERS, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("hits", [])
        if isinstance(hits, str):
            hits = _json.loads(hits)
            
        total_count = data.get("nbHits", len(hits))
        
        results = []
        for hit in hits:
            slug = hit.get("slug", "")
            if not slug: continue
            poster = hit.get("poster_url") or ""
            cover = hit.get("cover_url") or ""
            
            tags = hit.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            genres = ["Hentai"] + [t.title() for t in tags]
            
            results.append({
                "title": hit.get("name", ""),
                "japanese_title": "",
                "slug": slug,
                "url": f"https://hanime.tv/videos/hentai/{slug}",
                "poster": poster or cover,
                "sub_episodes": "1",
                "dub_episodes": "",
                "total_episodes": "1",
                "year": str(hit.get("released_at_unix", "")),
                "type": "OVA",
                "rating": "18+",
                "genres": genres,
            })
            
        return {
            "total": total_count,
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_hanime(slug):
    try:
        url = f"{HANIME_API_BASE}/video?id={slug}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        hentai_video = data.get("hentai_video", {})
        if not hentai_video:
            return {"error": "Video details not found"}, 404
            
        ani_id = hentai_video.get("slug", slug)
        title = hentai_video.get("name", "")
        desc = hentai_video.get("description", "")
        
        if desc:
            desc = re.sub('<[^<]+?>', '', desc).strip()
            
        poster = hentai_video.get("poster_url", "")
        cover = hentai_video.get("cover_url", "")
        
        detail = {
            "studio": hentai_video.get("brand", "Unknown"),
            "released": hentai_video.get("released_at", "Unknown"),
            "views": str(hentai_video.get("views", "0")),
            "likes": str(hentai_video.get("likes", "0")),
            "dislikes": str(hentai_video.get("dislikes", "0")),
            "downloads": str(hentai_video.get("downloads", "0")),
            "genres": [tag.get("text", "") for tag in data.get("hentai_tags", [])]
        }
        
        return {
            "ani_id": ani_id,
            "title": title,
            "japanese_title": "",
            "description": desc,
            "poster": poster or cover,
            "banner": cover or poster,
            "sub_episodes": "1",
            "dub_episodes": "",
            "type": "OVA",
            "rating": "18+",
            "mal_score": str(hentai_video.get("likes", "N/A")),
            "detail": detail,
            "seasons": [],
        }
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes_hanime(slug):
    try:
        url = f"{HANIME_API_BASE}/video?id={slug}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        hentai_video = data.get("hentai_video", {})
        franchise_videos = data.get("hentai_franchise_hentai_videos", [])
        
        if not franchise_videos:
            return [{
                "number": "1",
                "slug": slug,
                "title": hentai_video.get("name", "Episode 1"),
                "japanese_title": "",
                "token": f"hanime:{slug}",
                "has_sub": True,
                "has_dub": False,
            }]
            
        sorted_videos = sorted(franchise_videos, key=lambda x: x.get("released_at_unix", 0))
        
        episodes = []
        for idx, v in enumerate(sorted_videos):
            ep_slug = v.get("slug")
            episodes.append({
                "number": str(idx + 1),
                "slug": ep_slug,
                "title": v.get("name", f"Episode {idx + 1}"),
                "japanese_title": "",
                "token": f"hanime:{ep_slug}",
                "has_sub": True,
                "has_dub": False,
            })
            
        return episodes
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_servers_hanime(ep_token):
    try:
        if not ep_token.startswith("hanime:"):
            return {"error": "Invalid episode token for hanime"}, 400
        slug = ep_token.split("hanime:")[1]
        
        return {
            "watching": "HAnime Stream",
            "servers": {
                "sub": [
                    {
                        "name": "Shiva Server",
                        "server_id": "hanime",
                        "episode_id": slug,
                        "link_id": ep_token,
                    }
                ]
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_hanime_source(link_id):
    try:
        slug = link_id.split("hanime:")[1]
        url = f"{HANIME_API_BASE}/video?id={slug}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        manifest = data.get("videos_manifest", {})
        servers = manifest.get("servers", [])
        sources = []
        if servers:
            for stream in servers[0].get("streams", []):
                u = stream.get("url")
                if u:
                    sources.append({
                        "file": u,
                        "type": "hls",
                        "label": f"{stream.get('height')}p" if stream.get('height') else "Auto"
                    })
        
        hentai_video = data.get("hentai_video", {})
        video_id = hentai_video.get("id", "")
        poster = hentai_video.get("poster_url", "")
        from urllib.parse import quote
        encoded_poster = quote(poster) if poster else ""
        embed_url = f"https://player.hanime.tv/?&#v2,{video_id},{slug},{encoded_poster},no"
        
        return {
            "embed_url": embed_url,
            "skip": {},
            "sources": sources,
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
