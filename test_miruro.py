import json
from backend.scrapers.miruro import fetch_episodes_miruro, fetch_servers_miruro, resolve_source_miruro

# Test Miruro with the anime's ID (maybe the slug works for Miruro too, or maybe we need to search first)
from backend.scrapers.miruro import search_anime_miruro
print("Searching Miruro...")
search = search_anime_miruro("the oblivious saint cant contain her power")
print(json.dumps(search, indent=2))
if search.get("results"):
    ani_id = search["results"][0]["id"]
    print(f"\nFetching episodes for: {ani_id}")
    eps = fetch_episodes_miruro(ani_id)
    print(json.dumps(eps, indent=2))
    
    if eps:
        ep_id = eps[0]["id"]
        print(f"\nFetching servers for: {ep_id}")
        servers = fetch_servers_miruro(ep_id)
        print(json.dumps(servers, indent=2))
