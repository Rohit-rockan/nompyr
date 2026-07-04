import requests
from flask import Blueprint, jsonify, request
from config import Config
from core.cache import cache
from core.http_client import http_client
from core.database import get_db
from content_service.episodes.api import api_anime_info

reviews_bp = Blueprint("reviews", __name__)

def _get_mal_id_from_title(title):
    try:
        url = f"{Config.JIKAN_BASE_URL}/anime?q={title}&limit=1"
        r = http_client.jikan.get(url, timeout=Config.API_TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return data[0].get("mal_id")
    except Exception as e:
        print("Error fetching MAL ID for title:", e)
    return None

@reviews_bp.route("/api/reviews/<path:slug>", methods=["GET"])
def api_reviews(slug):
    cache_key = f"reviews:{slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    try:
        title = request.args.get("title")
        if not title:
            # If no title is provided, try to fetch info for the slug
            res = api_anime_info(slug)
            if hasattr(res, "get_json"):
                info = res.get_json()
                if info and "title" in info:
                    title = info["title"]
                    
        mal_id = None
        if slug.startswith("jikan:"):
            mal_id = slug.split("jikan:")[1]
        elif title:
            mal_id = _get_mal_id_from_title(title)
            
        if not mal_id:
            return jsonify({"success": False, "error": "Could not determine MAL ID"}), 404
            
        url = f"{Config.JIKAN_BASE_URL}/anime/{mal_id}/reviews"
        r = http_client.jikan.get(url, timeout=Config.API_TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("data", [])
            reviews = []
            for item in data:
                reviews.append({
                    "id": item.get("mal_id"),
                    "author": item.get("user", {}).get("username"),
                    "avatar": item.get("user", {}).get("images", {}).get("jpg", {}).get("image_url"),
                    "score": item.get("score"),
                    "content": item.get("review"),
                    "date": item.get("date"),
                    "tags": item.get("tags", [])
                })
                
            # Fetch local reviews
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM reviews WHERE ani_id = ? ORDER BY created_at DESC", (slug,))
                for row in cursor.fetchall():
                    reviews.append({
                        "id": f"local_{row['id']}",
                        "author": row["username"],
                        "avatar": None,
                        "score": row["rating"],
                        "content": row["comment"],
                        "date": row["created_at"],
                        "tags": ["Local User"]
                    })
            except Exception as db_e:
                print("Error fetching local reviews:", db_e)
                
            res_data = {"success": True, "reviews": reviews}
            cache.set(cache_key, res_data, timeout=Config.CACHE_TTL_DETAILS)
            return jsonify(res_data)
            
    except Exception as e:
        print("Error fetching reviews:", e)
        return jsonify({"success": False, "error": str(e)}), 500
        
    return jsonify({"success": True, "reviews": []})
