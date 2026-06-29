# ==============================================================================
# ROUTES — Anime Recommendations
# ==============================================================================
# Purpose:
#     Blueprint for recommendation routes: description-based TF-IDF
#     recommendations and Jikan-based related anime lookups.
#
# Need:
#     Powers the AI Recommender feature that lets users discover anime
#     by describing what they want to watch, and the "Similar Anime"
#     section on detail pages.
# ==============================================================================

import time

from flask import Blueprint, jsonify, request
import requests as _requests

from config import Config
from core import cache
from services.recommender import AnimeRecommender, find_local_slug_by_title
from services.jikan import map_jikan_to_nompyr

recs_bp = Blueprint("recommendations", __name__)

# Shared recommender instance
_anime_recommender = AnimeRecommender()


@recs_bp.route("/api/recommendations/description", methods=["GET"])
def api_recommend_description():
    """
    Description-based TF-IDF recommendation route.

    Detailed Use:
        Uses the internal TF-IDF Recommender engine to match a natural
        language plot description against a dataset of top-rated anime
        from Jikan.

    Need:
        Allows users to discover new shows based on specific moods,
        settings, or narrative tropes rather than just search keywords.
    """
    desc = request.args.get("description", "").strip()
    if not desc or len(desc) < 3:
        return jsonify({"success": True, "results": []})

    cache_key = f"recs_desc:{desc.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    headers = {"User-Agent": Config.DEFAULT_USER_AGENT}

    try:
        anime_data = []
        for page in (1, 2):
            r = _requests.get(
                f"{Config.JIKAN_BASE_URL}/top/anime?page={page}&limit=25",
                headers=headers,
                timeout=Config.API_TIMEOUT,
            )
            if r.status_code == 200:
                data = r.json().get("data", [])
                for item in data:
                    mapped = map_jikan_to_nompyr(item)
                    anime_data.append(mapped)
            time.sleep(Config.JIKAN_RATE_LIMIT_DELAY)

        if not anime_data:
            raise Exception("No anime data available for recommendations")

        results = _anime_recommender.recommend_by_description(desc, anime_data, top_n=12)

        res = {"success": True, "results": results}
        cache.set(cache_key, res, timeout=Config.CACHE_TTL_RECOMMENDATIONS)
        return jsonify(res)

    except Exception as e:
        print("Error in description recommender:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@recs_bp.route("/api/recommendations/anime", methods=["GET"])
def api_recommend_anime():
    """
    Related anime recommendations route (via Jikan/MAL).

    Detailed Use:
        Fetches related anime recommendations from Jikan (MAL) based on
        a specified anime title. Searches for the MAL ID first, then
        fetches the recommendations endpoint.

    Need:
        Enables the recommendation engine's 'Relationship Match' feature
        on the detail page.
    """
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "Anime title is required"}), 400

    cache_key = f"recs_anime:{title}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    recommendations = []
    try:
        search_url = f"{Config.JIKAN_BASE_URL}/anime"
        r = _requests.get(search_url, params={"q": title, "limit": 1}, timeout=Config.API_TIMEOUT)
        if r.status_code == 200:
            search_data = r.json().get("data", [])
            if search_data:
                mal_id = search_data[0].get("mal_id")

                recs_url = f"{Config.JIKAN_BASE_URL}/anime/{mal_id}/recommendations"
                r_recs = _requests.get(recs_url, timeout=Config.API_TIMEOUT)
                if r_recs.status_code == 200:
                    recs_data = r_recs.json().get("data", [])
                    for rec in recs_data[:12]:
                        entry = rec.get("entry", {})
                        rec_title = entry.get("title", "")
                        rec_images = (
                            entry.get("images", {}).get("jpg", {}).get("image_url", "")
                        )

                        local_slug = find_local_slug_by_title(rec_title)

                        recommendations.append({
                            "title": rec_title,
                            "japanese_title": "",
                            "slug": local_slug or f"search-fallback:{rec_title}",
                            "id": local_slug or f"search-fallback:{rec_title}",
                            "poster": rec_images,
                            "sub_episodes": "1",
                            "dub_episodes": "",
                            "total_episodes": "1",
                            "year": "",
                            "type": "TV",
                            "rating": "",
                            "score": "N/A",
                        })
    except Exception as e:
        print("Error fetching Jikan recommendations:", e)

    res = {"success": True, "results": recommendations}
    cache.set(cache_key, res, timeout=Config.CACHE_TTL_RECOMMENDATIONS)
    return jsonify(res)
