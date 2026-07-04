import os
import shutil

BASE_DIR = r"e:\nompyr\backend"

dirs_to_create = [
    "core_website/auth",
    "core_website/profiles",
    "core_website/bookmarks",
    "core_website/continue_watching",
    "content_service/metadata",
    "content_service/episodes",
    "content_service/genres",
    "content_service/search",
    "scraper_service/sources",
    "streaming_service/server_selection",
    "streaming_service/playlist_handling",
    "background_workers/tasks",
    "monitoring",
    "admin_dashboard"
]

for d in dirs_to_create:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
    init_file = os.path.join(BASE_DIR, d, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass

# Create top level __init__.py files
for d in ["core_website", "content_service", "scraper_service", "streaming_service", "background_workers"]:
    init_file = os.path.join(BASE_DIR, d, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass

moves = {
    # 1. core_website
    "routes/history.py": "core_website/continue_watching/api.py",
    
    # 2. content_service
    "services/anilist.py": "content_service/metadata/anilist.py",
    "services/jikan.py": "content_service/metadata/jikan.py",
    "routes/anime.py": "content_service/episodes/api.py",
    "routes/jikan_routes.py": "content_service/genres/api.py",
    "routes/search.py": "content_service/search/api.py",
    "routes/recommendations.py": "content_service/genres/recommendations.py",
    
    # 3. scraper_service
    "scrapers/anikototv.py": "scraper_service/sources/anikototv.py",
    "scrapers/animedekho.py": "scraper_service/sources/animedekho.py",
    # move any other scrapers
    
    # 4. streaming_service
    "routes/source.py": "streaming_service/server_selection/api.py",
    "routes/proxy.py": "streaming_service/playlist_handling/api.py",
    
    # 7. admin_dashboard
    "routes/admin.py": "admin_dashboard/api.py",
    
    # Not explicitly mentioned but probably need moving
    "routes/reviews.py": "content_service/metadata/reviews.py", # or somewhere
    "routes/home.py": "core_website/home.py", 
}

# Move other scrapers dynamically
if os.path.exists(os.path.join(BASE_DIR, "scrapers")):
    for file in os.listdir(os.path.join(BASE_DIR, "scrapers")):
        if file.endswith(".py") and file != "__init__.py":
            old_path = f"scrapers/{file}"
            new_path = f"scraper_service/sources/{file}"
            if old_path not in moves:
                moves[old_path] = new_path

for old_sub, new_sub in moves.items():
    old_path = os.path.join(BASE_DIR, old_sub)
    new_path = os.path.join(BASE_DIR, new_sub)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Moved {old_sub} to {new_sub}")
    else:
        print(f"Skipped {old_sub} (not found)")

print("Done moving files.")
