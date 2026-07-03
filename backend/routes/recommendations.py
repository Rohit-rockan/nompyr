import requests
from flask import Blueprint, jsonify, request
from config import Config
from core.cache import cache
from core.http_client import http_client

recommendations_bp = Blueprint("recommendations", __name__)

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

@recommendations_bp.route("/api/recommendations/anime", methods=["GET"])
def api_recommendations():
    title = request.args.get("title")
    if not title:
        return jsonify({"success": False, "error": "Title parameter required"}), 400
        
    cache_key = f"recommendations:{title}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)
        
    try:
        mal_id = _get_mal_id_from_title(title)
        if not mal_id:
            return jsonify({"success": False, "error": "Could not find anime on MAL"}), 404
            
        url = f"{Config.JIKAN_BASE_URL}/anime/{mal_id}/recommendations"
        r = http_client.jikan.get(url, timeout=Config.API_TIMEOUT)
        if r.status_code == 200:
            data = r.json().get("data", [])
            from services.jikan import map_jikan_to_nompyr
            recs = []
            for item in data:
                entry = item.get("entry")
                if entry:
                    # Fake a full item so map_jikan_to_nompyr works properly
                    fake_item = {
                        "mal_id": entry.get("mal_id"),
                        "title": entry.get("title"),
                        "images": entry.get("images"),
                        "type": "TV",
                        "status": "Completed"
                    }
                    recs.append(map_jikan_to_nompyr(fake_item))
                    
            res_data = {"success": True, "results": recs}
            cache.set(cache_key, res_data, timeout=Config.CACHE_TTL_RECOMMENDATIONS)
            return jsonify(res_data)
            
    except Exception as e:
        print("Error fetching recommendations:", e)
        return jsonify({"success": False, "error": str(e)}), 500
        
    return jsonify({"success": True, "results": []})
