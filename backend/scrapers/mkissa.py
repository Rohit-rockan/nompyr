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
        return {"error": str(e)}

def scrape_home_mkissa():
    try:
        # Search/Recent hash: a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c
        variables = {"search": {"sortBy": "Recent"}, "limit": 20, "page": 1, "translationType": "sub"}
        hash_val = "a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"success": False, "error": data["error"]}
            
        edges = data.get("data", {}).get("shows", {}).get("edges", [])
        
        latest = []
        for edge in edges:
            latest.append({
                "title": edge.get("englishName") or edge.get("name") or "",
                "japanese_title": edge.get("nativeName") or "",
                "poster": edge.get("thumbnail", ""),
                "url": f"{MKISSA_URL}anime/{edge.get('_id')}",
                "slug": edge.get("_id"),
                "type": "TV",
                "sub_episodes": str(edge.get("availableEpisodes", {}).get("sub", "")),
                "dub_episodes": str(edge.get("availableEpisodes", {}).get("dub", "")),
            })
            
        return {"success": True, "data": {"banner": [], "latest_updates": latest}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_mkissa(query):
    try:
        # We can use the same hash but provide query
        variables = {"search": {"query": query}, "limit": 20, "page": 1, "translationType": "sub"}
        hash_val = "a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"success": False, "error": data["error"]}
            
        edges = data.get("data", {}).get("shows", {}).get("edges", [])
        
        results = []
        for edge in edges:
            results.append({
                "title": edge.get("englishName") or edge.get("name") or "",
                "japanese_title": edge.get("nativeName") or "",
                "poster": edge.get("thumbnail", ""),
                "url": f"{MKISSA_URL}anime/{edge.get('_id')}",
                "slug": edge.get("_id"),
                "type": "TV",
                "sub_episodes": str(edge.get("availableEpisodes", {}).get("sub", "")),
                "dub_episodes": str(edge.get("availableEpisodes", {}).get("dub", "")),
            })
            
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

def scrape_anime_info_mkissa(slug):
    try:
        variables = {"_id": slug}
        hash_val = "ddd45aafa6c07d1cb5fbf90050fa010b885e10994f171223b6bdb888e164ce03"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"success": False, "error": data["error"]}
            
        show = data.get("data", {}).get("show", {})
        
        info = {
            "title": show.get("englishName") or show.get("name") or "",
            "japanese_title": show.get("nativeName") or "",
            "poster": show.get("thumbnail", ""),
            "description": show.get("description", ""),
            "url": f"{MKISSA_URL}anime/{slug}",
            "slug": slug,
            "type": show.get("type", "TV"),
            "release": show.get("season", {}).get("year", ""),
            "status": show.get("status", ""),
            "genres": show.get("genres", []),
        }
        
        return {"success": True, "data": info}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_episodes_mkissa(slug):
    try:
        variables = {"_id": slug}
        hash_val = "ddd45aafa6c07d1cb5fbf90050fa010b885e10994f171223b6bdb888e164ce03"
        
        data = _gql_request(variables, hash_val)
        if "error" in data:
            return {"success": False, "error": data["error"]}
            
        show = data.get("data", {}).get("show", {})
        available = show.get("availableEpisodesDetail", {}).get("sub", [])
        
        eps = []
        for ep in available:
            eps.append({
                "number": ep,
                "title": f"Episode {ep}",
                "id": ep,
                "url": f"{MKISSA_URL}watch/{slug}/ep-{ep}"
            })
            
        eps.reverse() # typically APIs return newest first or oldest first. 
        # let's sort them numerically
        eps.sort(key=lambda x: float(x["number"]) if x["number"].replace('.','').isdigit() else 0)
            
        return {"success": True, "data": eps}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_servers_mkissa(episode_id):
    # Mkissa is a catalog site and does not offer streaming directly.
    return {"success": True, "data": {"sub": [], "dub": []}}

def resolve_source_mkissa(server_id, episode_id=None):
    return {"success": False, "error": "No streaming available on Mkissa"}

if __name__ == "__main__":
    print("Testing Home...")
    home = scrape_home_mkissa()
    print("Latest:", len(home.get("data", {}).get("latest_updates", [])))
    
    print("\\nTesting Search...")
    search = search_mkissa("naruto")
    print("Found:", len(search.get("data", [])))
    if search.get("data"):
        print("First:", search["data"][0])
        
    print("\\nTesting Info...")
    info = scrape_anime_info_mkissa("DN3dcZSKe2tDtPsny")
    print(info.get("data", {}).get("title"))
    
    print("\\nTesting Episodes...")
    eps = fetch_episodes_mkissa("DN3dcZSKe2tDtPsny")
    print("Found:", len(eps.get("data", [])))
