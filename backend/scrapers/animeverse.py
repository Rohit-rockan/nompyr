def scrape_home_animeverse():
    return {
        "banner": [],
        "latest_updates": [],
        "top_trending": {
            "NOW": [],
            "DAY": [],
            "WEEK": [],
            "MONTH": []
        },
        "popular": [],
        "upcoming": []
    }

def search_anime_animeverse(keyword, page=1):
    return {
        "total": 0,
        "page": page,
        "per_page": 20,
        "results": []
    }

def scrape_anime_info_animeverse(slug):
    return {
        "ani_id": slug,
        "title": slug,
        "japanese_title": "",
        "description": "",
        "poster": "",
        "banner": "",
        "sub_episodes": "",
        "dub_episodes": "",
        "type": "TV",
        "rating": "",
        "mal_score": "",
        "detail": {
            "studio": "",
            "released": "",
            "views": "",
            "likes": "",
            "dislikes": "",
            "downloads": "",
            "genres": []
        },
        "seasons": []
    }

def fetch_episodes_animeverse(slug):
    return []

def fetch_servers_animeverse(ep_token):
    return {
        "watching": "Animeverse",
        "servers": {
            "sub": [],
            "dub": []
        }
    }

def resolve_animeverse_source(link_id):
    return {
        "embed_url": "",
        "skip": {},
        "sources": [],
        "tracks": [],
        "download": ""
    }
