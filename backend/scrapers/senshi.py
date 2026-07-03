import json
import cloudscraper

BASE_URL = "https://senshi.live"

def get_scraper():
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

def scrape_home_senshi():
    scraper = get_scraper()
    
    try:
        popular_req = scraper.post(f"{BASE_URL}/anime/filter", json={
            "page": 1,
            "limit": 24,
            "sortBy": "score"
        }).json()
        
        latest_req = scraper.post(f"{BASE_URL}/anime/filter", json={
            "page": 1,
            "limit": 24,
            "sortBy": "latest"
        }).json()
        
        pop_items = []
        for anime in popular_req.get('data', []):
            image = anime.get("anime_picture", "")
            if image and not image.startswith("http"):
                image = BASE_URL + image
                
            pop_items.append({
                "title": anime.get("title") or anime.get("title_english") or "Unknown",
                "japanese_title": anime.get("title_english") or "",
                "poster": image,
                "url": f"/anime/senshi/{anime.get('public_id')}",
                "slug": anime.get('public_id'),
                "current_episode": "",
                "sub_episodes": str(anime.get("ani_episodes", "")),
                "dub_episodes": "",
                "type": anime.get("type", "TV")
            })
            
        latest_items = []
        for anime in latest_req.get('data', []):
            image = anime.get("anime_picture", "")
            if image and not image.startswith("http"):
                image = BASE_URL + image
                
            latest_items.append({
                "title": anime.get("title") or anime.get("title_english") or "Unknown",
                "japanese_title": anime.get("title_english") or "",
                "poster": image,
                "url": f"/anime/senshi/{anime.get('public_id')}",
                "slug": anime.get('public_id'),
                "current_episode": "",
                "sub_episodes": str(anime.get("ani_episodes", "")),
                "dub_episodes": "",
                "type": anime.get("type", "TV")
            })
            
        return {
            "banner": pop_items[:5] if pop_items else [],
            "latest_updates": latest_items,
            "top_trending": {
                "NOW": pop_items[:15],
                "DAY": pop_items[:15],
                "WEEK": pop_items[:15],
                "MONTH": pop_items[:15]
            },
            "popular": pop_items,
            "upcoming": []
        }
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_senshi(keyword, page=1):
    scraper = get_scraper()
    try:
        req = scraper.post(f"{BASE_URL}/anime/filter", json={
            "searchTerm": keyword,
            "page": page,
            "limit": 20
        }).json()
        
        results = []
        for anime in req.get('data', []):
            image = anime.get("anime_picture", "")
            if image and not image.startswith("http"):
                image = BASE_URL + image
                
            results.append({
                "title": anime.get("title") or anime.get("title_english") or "Unknown",
                "japanese_title": anime.get("title_english") or "",
                "slug": anime.get('public_id'),
                "url": f"/anime/senshi/{anime.get('public_id')}",
                "poster": image,
                "sub_episodes": str(anime.get("ani_episodes", "")),
                "dub_episodes": "",
                "total_episodes": str(anime.get("ani_episodes", "")),
                "year": str(anime.get("ani_year", "")),
                "type": anime.get("type", "TV"),
                "rating": "",
                "genres": []
            })
            
        return {
            "total": len(results),
            "page": page,
            "per_page": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_anime_info_senshi(slug):
    scraper = get_scraper()
    
    info_url = f"{BASE_URL}/anime/{slug}"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return {"error": "Not found"}, 404
        
    anime_data = req.json()
    internal_id = anime_data.get("id")
    
    image = anime_data.get("anime_picture", "")
    if image and not image.startswith("http"):
        image = BASE_URL + image
        
    return {
        "ani_id": slug,
        "title": anime_data.get("title") or anime_data.get("title_english") or "Unknown",
        "japanese_title": anime_data.get("title_english") or "",
        "description": anime_data.get("ani_description", ""),
        "poster": image,
        "banner": image,
        "sub_episodes": str(anime_data.get("ani_episodes", "")),
        "dub_episodes": "",
        "type": anime_data.get("type", "TV"),
        "rating": "",
        "mal_score": "",
        "detail": {
            "studio": "",
            "released": str(anime_data.get("ani_year", "")),
            "views": "",
            "likes": "",
            "dislikes": "",
            "downloads": "",
            "genres": []
        },
        "seasons": []
    }

def fetch_episodes_senshi(slug):
    scraper = get_scraper()
    
    info_url = f"{BASE_URL}/anime/{slug}"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return []
        
    anime_data = req.json()
    internal_id = anime_data.get("id")
    
    eps_req = scraper.get(f"{BASE_URL}/episodes/{internal_id}")
    if eps_req.status_code != 200:
        return []
        
    episodes_data = eps_req.json()
    
    episodes = []
    for ep in episodes_data:
        ep_id = ep.get("ep_id")
        episodes.append({
            "number": str(ep_id),
            "slug": str(ep_id),
            "title": ep.get("ep_title") or f"Episode {ep_id}",
            "japanese_title": "",
            "token": f"senshi:{internal_id}/{ep_id}",
            "has_sub": True,
            "has_dub": False
        })
        
    episodes.sort(key=lambda x: float(x["number"]) if x["number"].replace('.', '', 1).isdigit() else 0)
    return episodes

def fetch_servers_senshi(ep_token):
    scraper = get_scraper()
    
    try:
        if not ep_token.startswith("senshi:"):
            return {"error": "Invalid token"}, 400
        episode_id = ep_token.split("senshi:")[1]
        
        req = scraper.get(f"{BASE_URL}/episode-embeds/{episode_id}")
        if req.status_code != 200:
            return {"error": "Not found"}, 404
            
        data = req.json()
        servers = []
        
        for server in data:
            if server.get("url"):
                url = server.get("url")
                servers.append({
                    "name": server.get("status", "Server") + " (Senshi)",
                    "server_id": url,
                    "episode_id": episode_id,
                    "link_id": f"senshi_server:{url}"
                })
                
        return {
            "watching": "Senshi Player",
            "servers": {
                "sub": servers,
                "dub": []
            }
        }
    except Exception as e:
        return {"error": str(e)}, 500

def resolve_senshi_source(link_id):
    try:
        if not link_id.startswith("senshi_server:"):
            return {"error": "Invalid token"}, 400
        server_url = link_id.split("senshi_server:")[1]
        
        return {
            "embed_url": server_url,
            "skip": {},
            "sources": [],
            "tracks": [],
            "download": ""
        }
    except Exception as e:
        return {"error": str(e)}, 500
