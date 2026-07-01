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
    
    # Senshi.live doesn't have a single /home endpoint with all sections easily accessible like that.
    # We can fetch 'latest-episodes' and 'anime/recently-added'.
    
    # We'll just fetch a few endpoints to compose a home response.
    sections = []
    
    try:
        # Recently added (often maps to "Recent Episodes" or "Latest")
        recent = scraper.get(f"{BASE_URL}/episode-embeds/latest").json()
        
        items = []
        for item in recent:
            # Note: /episode-embeds/latest structure is a bit different, need to map it
            # Actually, let's use the /anime/filter with sorting to get recent.
            pass
            
        # Let's use the filter API to get recent updates/trending.
        # Top Anime (Trending/Popular)
        popular_req = scraper.post(f"{BASE_URL}/anime/filter", json={
            "page": 1,
            "limit": 10,
            "sortBy": "score" # Assuming score or views
        }).json()
        
        pop_items = []
        for anime in popular_req.get('data', []):
            pop_items.append({
                "id": anime.get("public_id"),
                "title": anime.get("title") or anime.get("title_english"),
                "image": BASE_URL + anime.get("anime_picture", "") if anime.get("anime_picture") and not anime.get("anime_picture").startswith("http") else anime.get("anime_picture"),
                "url": f"/anime/senshi/{anime.get('public_id')}"
            })
            
        if pop_items:
            sections.append({
                "title": "Popular",
                "items": pop_items
            })
            
    except Exception as e:
        print(f"Error fetching senshi home: {e}")
        
    return sections

def search_senshi(query):
    scraper = get_scraper()
    try:
        req = scraper.post(f"{BASE_URL}/anime/filter", json={
            "searchTerm": query,
            "page": 1,
            "limit": 20
        }).json()
        
        results = []
        for anime in req.get('data', []):
            results.append({
                "id": anime.get("public_id"),
                "title": anime.get("title") or anime.get("title_english"),
                "image": BASE_URL + anime.get("anime_picture", "") if anime.get("anime_picture") and not anime.get("anime_picture").startswith("http") else anime.get("anime_picture"),
                "url": f"/anime/senshi/{anime.get('public_id')}",
                "type": anime.get("type", "TV"),
                "year": anime.get("ani_year", "")
            })
        return results
    except Exception as e:
        print(f"Senshi search error: {e}")
        return []

def scrape_anime_info_senshi(anime_id):
    scraper = get_scraper()
    
    info_url = f"{BASE_URL}/anime/{anime_id}"
    req = scraper.get(info_url)
    
    if req.status_code != 200:
        return None
        
    anime_data = req.json()
    internal_id = anime_data.get("id")
    
    info = {
        "id": anime_data.get("public_id"),
        "title": anime_data.get("title") or anime_data.get("title_english"),
        "image": BASE_URL + anime_data.get("anime_picture", "") if anime_data.get("anime_picture") and not anime_data.get("anime_picture").startswith("http") else anime_data.get("anime_picture"),
        "description": anime_data.get("ani_description", ""),
        "status": anime_data.get("ani_status", ""),
        "type": anime_data.get("type", ""),
        "totalEpisodes": anime_data.get("ani_episodes", ""),
        "episodes": []
    }
    
    # Fetch episodes using the internal numeric ID
    eps_req = scraper.get(f"{BASE_URL}/episodes/{internal_id}")
    if eps_req.status_code == 200:
        episodes_data = eps_req.json()
        for ep in episodes_data:
            info["episodes"].append({
                "id": f"{internal_id}/{ep.get('ep_id')}",
                "number": ep.get("ep_id"),
                "title": ep.get("ep_title", f"Episode {ep.get('ep_id')}"),
            })
            
    return info

def fetch_servers_senshi(episode_id):
    # episode_id is in format {internal_id}/{ep_id}
    scraper = get_scraper()
    
    try:
        req = scraper.get(f"{BASE_URL}/episode-embeds/{episode_id}")
        if req.status_code != 200:
            return []
            
        data = req.json()
        servers = []
        
        # data is a list of server objects
        for server in data:
            if server.get("url"):
                servers.append({
                    "name": server.get("status", "Server") + " (Senshi)",
                    "url": server.get("url"),
                    "type": "iframe" if "youtube.com" in server.get("url") else "hls" 
                    # Assuming senshi provides direct HLS or MP4 in 'url' based on tests.
                })
        return servers
    except Exception as e:
        print(f"Senshi server fetch error: {e}")
        return []

def resolve_source_senshi(server_url):
    return server_url
