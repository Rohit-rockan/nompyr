import json
from backend.scrapers.miruro import search_anime_miruro, fetch_episodes_miruro, fetch_servers_miruro, resolve_source_miruro

print("Searching Miruro for '86'...")
search = search_anime_miruro("86")
print(json.dumps(search, indent=2))
if search.get("results"):
    # Find the exact match or first one
    match = next((res for res in search["results"] if "86" in res["title"]), search["results"][0])
    ani_id = match["id"]
    print(f"\nFetching episodes for: {ani_id} ({match['title']})")
    eps = fetch_episodes_miruro(ani_id.split('miruro:')[1] if 'miruro:' in ani_id else ani_id)
    print(json.dumps(eps, indent=2))
    
    if eps:
        ep_id = eps[0]["token"]
        print(f"\nFetching servers for: {ep_id}")
        servers = fetch_servers_miruro(ep_id)
        print(json.dumps(servers, indent=2))
        
        if servers and servers.get("servers") and servers["servers"].get("sub") and len(servers["servers"]["sub"]) > 0:
            link_id = servers["servers"]["sub"][0]["link_id"]
            print(f"\nResolving source for link_id: {link_id}")
            source = resolve_source_miruro(link_id)
            print(json.dumps(source, indent=2))
