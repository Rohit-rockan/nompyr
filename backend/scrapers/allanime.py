# ==============================================================================
# SCRAPER — ALLANIME
# ==============================================================================
import requests
import json
import re
from bs4 import BeautifulSoup
from config import Config

ALLANIME_API_URL = "https://api.allanime.day/api"
HEADERS = {
    "User-Agent": Config.DEFAULT_USER_AGENT,
    "Referer": "https://allanime.day/"
}

def _gql_request(query, variables):
    payload = {
        "query": query,
        "variables": variables
    }
    r = requests.post(ALLANIME_API_URL, json=payload, headers=HEADERS, timeout=Config.SCRAPER_TIMEOUT)
    r.raise_for_status()
    return r.json()

def search_anime_allanime(query, page=1):
    try:
        gql_query = """
        query($search: SearchInput, $limit: Int, $page: Int, $translationType: VaildTranslationTypeEnumType) {
            shows(search: $search, limit: $limit, page: $page, translationType: $translationType) {
                edges {
                    _id
                    name
                    englishName
                    thumbnail
                    availableEpisodesDetail
                }
            }
        }
        """
        variables = {
            "search": {"allowAdult": False, "allowUnknown": False, "query": query},
            "limit": 20,
            "page": page,
            "translationType": "sub"
        }
        
        data = _gql_request(gql_query, variables)
        edges = data.get("data", {}).get("shows", {}).get("edges", [])
        
        results = []
        for edge in edges:
            results.append({
                "ani_id": f"allanime:{edge['_id']}",
                "title": edge.get("name") or edge.get("englishName") or "Unknown",
                "japanese_title": edge.get("nativeName") or "",
                "poster": edge.get("thumbnail") or "",
                "type": "TV",
                "score": "N/A",
                "sub_episodes": len(edge.get("availableEpisodesDetail", {}).get("sub", [])),
                "dub_episodes": len(edge.get("availableEpisodesDetail", {}).get("dub", []))
            })
            
        return {"results": results, "total": len(results)}
    except Exception as e:
        print("Error in search_anime_allanime:", e)
        return {"results": [], "total": 0}

def scrape_anime_info_allanime(slug):
    try:
        gql_query = """
        query ($showId: String!) {
            show(_id: $showId) {
                _id
                name
                englishName
                thumbnail
                description
                type
                season
                score
                status
            }
        }
        """
        variables = {"showId": slug}
        data = _gql_request(gql_query, variables)
        show = data.get("data", {}).get("show", {})
        
        if not show:
            return {"error": "Not found"}
            
        return {
            "title": show.get("name") or show.get("englishName") or "Unknown",
            "japanese_title": show.get("englishName") or "",
            "poster": show.get("thumbnail") or "",
            "description": show.get("description") or "No description",
            "type": show.get("type") or "TV",
            "season": show.get("season") or {} if isinstance(show.get("season"), dict) else "Unknown",
            "score": show.get("score") or "N/A",
            "status": show.get("status") or "Ongoing"
        }
    except Exception as e:
        return {"error": str(e)}

def fetch_episodes_allanime(slug):
    try:
        gql_query = """
        query ($showId: String!) {
            show(_id: $showId) {
                _id
                availableEpisodesDetail
            }
        }
        """
        variables = {"showId": slug}
        data = _gql_request(gql_query, variables)
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
                "token": f"allanime:{slug}:{ep}",
                "has_sub": True,
                "has_dub": False
            })
            
        eps.sort(key=lambda x: float(x["number"]) if x["number"].replace('.','',1).isdigit() else 0)
            
        return eps
    except Exception as e:
        return []

def fetch_servers_allanime(ep_token):
    return {
        "watching": "AllAnime (No Streaming, Captcha Required)",
        "servers": {
            "sub": [],
            "dub": []
        }
    }

def scrape_home_allanime():
    return {"banner": [], "latest_updates": []}

def resolve_allanime_source(link_id):
    return {"url": "", "quality": [], "headers": {}}

