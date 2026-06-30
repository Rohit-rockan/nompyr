import json
from backend.scrapers.animekai import resolve_source

url = "https://megaplay.buzz/stream/mal/62080/1/sub"
print(f"Resolving source for: {url}")
source = resolve_source(url)
print(json.dumps(source, indent=2))
