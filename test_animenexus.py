import json
from backend.scrapers.animenexus import search_anime_animenexus, fetch_episodes_animenexus, fetch_servers_animenexus

print("Searching animenexus...")
search = search_anime_animenexus("the oblivious saint cant contain her power")
print(json.dumps(search, indent=2))
if search.get("results"):
    ani_id = search["results"][0]["id"]
    print(f"\nFetching episodes for: {ani_id}")
    eps = fetch_episodes_animenexus(ani_id)
    print(json.dumps(eps, indent=2))
    
    if eps:
        ep_id = eps[0]["id"]
        print(f"\nFetching servers for: {ep_id}")
        servers = fetch_servers_animenexus(ep_id)
        print(json.dumps(servers, indent=2))
