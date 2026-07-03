import requests
import json

MKISSA_URL = "https://mkissa.to/"
API_URL = "https://api.allanime.day/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://mkissa.to",
    "Referer": "https://mkissa.to/",
}

def _gql_request(variables, hash_val):
    try:
        url = f"{API_URL}?variables={requests.utils.quote(json.dumps(variables))}&extensions={requests.utils.quote(json.dumps({'persistedQuery': {'version': 1, 'sha256Hash': hash_val}}))}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_home_mkissa():
    try:
        variables = {"search": {"sortBy": "Recent"}, "limit": 24, "page": 1, "translationType": "sub"}
        hash_val = "a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"error": data["error"]}, 500
            
        edges = data.get("data", {}).get("shows", {}).get("edges", [])
        
        latest = []
        for edge in edges:
            latest.append({
                "title": edge.get("englishName") or edge.get("name") or "",
                "japanese_title": edge.get("nativeName") or "",
                "poster": edge.get("thumbnail", ""),
                "url": f"/anime/mkissa/{edge.get('_id')}",
                "slug": edge.get("_id"),
                "current_episode": "",
                "sub_episodes": str(edge.get("availableEpisodes", {}).get("sub", "")),
                "dub_episodes": str(edge.get("availableEpisodes", {}).get("dub", "")),
                "type": "TV"
            })
            
        return {
            "banner": [],
            "latest_updates": latest,
            "top_trending": {
                "NOW": latest[:15],
                "DAY": latest[:15],
                "WEEK": latest[:15],
                "MONTH": latest[:15]
            },
            "popular": latest[:15],
            "upcoming": []
        }
    except Exception as e:
        return {"error": str(e)}, 500

def search_anime_mkissa(keyword, page=1):
    try:
        variables = {"search": {"query": keyword}, "limit": 20, "page": page, "translationType": "sub"}
        hash_val = "a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"error": data["error"]}, 500
            
        edges = data.get("data", {}).get("shows", {}).get("edges", [])
        
        results = []
        for edge in edges:
            results.append({
                "title": edge.get("englishName") or edge.get("name") or "",
                "japanese_title": edge.get("nativeName") or "",
                "slug": edge.get("_id"),
                "url": f"/anime/mkissa/{edge.get('_id')}",
                "poster": edge.get("thumbnail", ""),
                "sub_episodes": str(edge.get("availableEpisodes", {}).get("sub", "")),
                "dub_episodes": str(edge.get("availableEpisodes", {}).get("dub", "")),
                "total_episodes": "",
                "year": "",
                "type": "TV",
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

def scrape_anime_info_mkissa(slug):
    try:
        variables = {"_id": slug}
        hash_val = "ddd45aafa6c07d1cb5fbf90050fa010b885e10994f171223b6bdb888e164ce03"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"error": data["error"]}, 500
            
        show = data.get("data", {}).get("show", {})
        if not show:
            return {"error": "Not found"}, 404
        
        info = {
            "ani_id": slug,
            "title": show.get("englishName") or show.get("name") or "",
            "japanese_title": show.get("nativeName") or "",
            "description": show.get("description", ""),
            "poster": show.get("thumbnail", ""),
            "banner": show.get("thumbnail", ""),
            "sub_episodes": str(show.get("availableEpisodes", {}).get("sub", "")),
            "dub_episodes": str(show.get("availableEpisodes", {}).get("dub", "")),
            "type": show.get("type", "TV"),
            "rating": "",
            "mal_score": "",
            "detail": {
                "studio": "",
                "released": str(show.get("season", {}).get("year", "")),
                "views": "",
                "likes": "",
                "dislikes": "",
                "downloads": "",
                "genres": show.get("genres", []),
            },
            "seasons": [],
        }
        
        return info
    except Exception as e:
        return {"error": str(e)}, 500

def fetch_episodes_mkissa(slug):
    try:
        variables = {"_id": slug}
        hash_val = "ddd45aafa6c07d1cb5fbf90050fa010b885e10994f171223b6bdb888e164ce03"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return []
            
        show = data.get("data", {}).get("show", {})
        if not show:
            return []
            
        available = show.get("availableEpisodesDetail", {}).get("sub", [])
        
        eps = []
        for ep in available:
            eps.append({
                "number": str(ep),
                "slug": str(ep),
                "title": f"Episode {ep}",
                "japanese_title": "",
                "token": f"mkissa:{slug}:{ep}",
                "has_sub": True,
                "has_dub": False
            })
            
        eps.sort(key=lambda x: float(x["number"]) if x["number"].replace('.','',1).isdigit() else 0)
            
        return eps
    except Exception as e:
        return []

def fetch_servers_mkissa(ep_token):
    return {
        "watching": "Mkissa (No Streaming)",
        "servers": {
            "sub": [],
            "dub": []
        }
    }

def resolve_mkissa_source(link_id):
    return {"error": "No streaming available on Mkissa"}, 400
