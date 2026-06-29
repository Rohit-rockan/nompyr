# ==============================================================================
# ROUTES — Jikan Seasonal & Top Lists
# ==============================================================================
# Purpose:
#     Blueprint for the Jikan API integration route that provides
#     seasonal airing, upcoming, and top lifetime anime lists.
#
# Need:
#     Populates the home discover tabs with data when native scrapers
#     encounter network errors or service outages. Acts as a reliable
#     fallback data source using the public MAL/Jikan API.
# ==============================================================================

import time

from flask import Blueprint, jsonify
import requests as _requests

from config import Config
from core import cache
from services.jikan import map_jikan_to_nompyr

jikan_bp = Blueprint("jikan", __name__)


@jikan_bp.route("/api/jikan-lists", methods=["GET"])
def api_jikan_lists():
    """
    Jikan seasonal & top lists route.

    Detailed Use:
        Dispatches requests to Jikan to retrieve current season airing
        lists, upcoming season announcements, and top lifetime records,
        then packs them into categorized sections.

    Need:
        Required to populate the home discover tabs with data when native
        scrapers encounter network errors or service outages.
    """
    cache_key = "jikan_lists_v2"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    headers = {"User-Agent": Config.DEFAULT_USER_AGENT}

    try:
        r_now = _requests.get(
            f"{Config.JIKAN_BASE_URL}/seasons/now?limit=25",
            headers=headers,
            timeout=Config.API_TIMEOUT,
        )
        time.sleep(Config.JIKAN_SEASONAL_DELAY)

        r_upcoming = _requests.get(
            f"{Config.JIKAN_BASE_URL}/seasons/upcoming?limit=25",
            headers=headers,
            timeout=Config.API_TIMEOUT,
        )
        time.sleep(Config.JIKAN_SEASONAL_DELAY)

        r_top = _requests.get(
            f"{Config.JIKAN_BASE_URL}/top/anime?limit=25",
            headers=headers,
            timeout=Config.API_TIMEOUT,
        )

        new_releases = []
        upcoming = []
        completed = []

        if r_now.status_code == 200:
            for item in r_now.json().get("data", []):
                new_releases.append(map_jikan_to_nompyr(item, "Ongoing"))

        if r_upcoming.status_code == 200:
            for item in r_upcoming.json().get("data", []):
                upcoming.append(map_jikan_to_nompyr(item, "Upcoming"))

        if r_top.status_code == 200:
            for item in r_top.json().get("data", []):
                completed.append(map_jikan_to_nompyr(item, "Completed"))

        if not new_releases and not upcoming and not completed:
            raise Exception("Jikan API returned empty results")

        res = {
            "success": True,
            "newReleases": new_releases,
            "upcoming": upcoming,
            "completed": completed,
        }
        cache.set(cache_key, res, timeout=Config.CACHE_TTL_JIKAN_LISTS)
        return jsonify(res)

    except Exception as e:
        print("Error in Jikan lists fetch:", e)
        return jsonify({"success": False, "error": str(e)}), 500
