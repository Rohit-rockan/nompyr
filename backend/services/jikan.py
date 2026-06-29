# ==============================================================================
# SERVICES — Jikan (MyAnimeList) API Integration
# ==============================================================================
# Purpose:
#     Handles all interactions with the Jikan API (unofficial MAL API):
#     anime info lookups, episode lists, and data mapping from MAL's
#     format to Nompyr's internal schema.
#
# Need:
#     Jikan provides a rich fallback data source when native scrapers
#     are down or when users search by MAL ID. Also powers search
#     predictions, seasonal lists, and top anime charts.
# ==============================================================================

import time

from config import Config
from core.cache import cache
from core.http_client import http_client


# ==============================================================================
# SECTION 1: DATA MAPPING
# ==============================================================================

def map_jikan_to_nompyr(item, status_override=None):
    """
    Translate a Jikan API anime response into Nompyr's internal schema.

    Detailed Use:
        Maps MAL's nested data structures (images.jpg.large_image_url,
        genres[].name, studios[].name, aired.prop.from.year, etc.) into
        the flat, consistent schema used by the Nompyr frontend.

    Need:
        The frontend expects a uniform data shape regardless of data
        source. Without this mapping, Jikan results would crash the
        card renderer or display incorrectly.

    Args:
        item (dict): Raw Jikan API anime data object.
        status_override (str, optional): Force a specific status value
            (e.g., 'Ongoing', 'Upcoming', 'Completed').

    Returns:
        dict: Anime metadata in Nompyr's internal schema.
    """
    mal_id = item.get("mal_id")
    title = item.get("title") or "Untitled"
    jp_title = item.get("title_japanese") or title

    # Images
    poster = (
        item.get("images", {}).get("jpg", {}).get("large_image_url")
        or item.get("images", {}).get("jpg", {}).get("image_url")
        or ""
    )
    banner = poster

    # Genres
    genres = [g.get("name") for g in item.get("genres", []) if g.get("name")]

    # Studio
    studio = "Unknown"
    studios = item.get("studios", [])
    if studios:
        studio = studios[0].get("name") or "Unknown"

    # Status mapping
    status = status_override
    if not status:
        j_status = item.get("status", "").lower()
        if "currently airing" in j_status:
            status = "Ongoing"
        elif "finished" in j_status:
            status = "Completed"
        elif "not yet aired" in j_status:
            status = "Upcoming"
        else:
            status = "Completed"

    # Year extraction
    year = item.get("year")
    if not year:
        aired_from = item.get("aired", {}).get("prop", {}).get("from", {})
        if aired_from:
            year = aired_from.get("year")
    year = year or 2026

    # Episodes
    episodes = item.get("episodes") or 1

    return {
        "id": f"jikan:{mal_id}",
        "title": title,
        "jpTitle": jp_title,
        "type": item.get("type") or "TV",
        "status": status,
        "year": year,
        "season": item.get("season") or "Spring",
        "rating": item.get("rating") or "PG-13",
        "score": item.get("score") or "N/A",
        "duration": item.get("duration") or "24m",
        "studio": studio,
        "genres": genres,
        "language": ["Sub", "Dub"],
        "episodes": episodes,
        "latestEpisode": (
            episodes if status == "Completed"
            else (item.get("episodes") or 1)
        ),
        "updatedAt": time.strftime("%Y-%m-%d"),
        "schedule": "TBA",
        "color": "#7c3aed",
        "accent": "#f97316",
        "poster": poster,
        "banner": banner,
        "description": item.get("synopsis") or "No description available.",
        "tags": [g.get("name") for g in item.get("genres", [])][:3],
        "sourceHealth": "Healthy",
    }


# ==============================================================================
# SECTION 2: ANIME INFO & EPISODES FETCHING
# ==============================================================================

def scrape_anime_info_jikan(mal_id):
    """
    Fetch detailed anime info from Jikan API by MAL ID.

    Detailed Use:
        Queries api.jikan.moe/v4/anime/{mal_id} and maps the response
        to Nompyr's schema using map_jikan_to_nompyr().

    Need:
        Renders rich detail pages for shows resolved via MAL prediction
        queries rather than local scrapers.

    Args:
        mal_id (str|int): The MyAnimeList ID.

    Returns:
        dict: Anime details in Nompyr schema, or error dict on failure.
    """
    cache_key = f"jikan_details:{mal_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{Config.JIKAN_BASE_URL}/anime/{mal_id}"
    try:
        r = http_client.jikan.get(
            url,
            headers={"User-Agent": Config.DEFAULT_USER_AGENT},
            timeout=Config.API_TIMEOUT,
        )
        if r.status_code == 200:
            item = r.json().get("data", {})
            mapped = map_jikan_to_nompyr(item)
            cache.set(cache_key, mapped, timeout=Config.CACHE_TTL_JIKAN_DETAILS)
            return mapped
    except Exception as e:
        print("Error fetching Jikan details:", e)

    return {"error": "Failed to fetch details from Jikan API"}


def fetch_episodes_jikan(mal_id):
    """
    Fetch episode list from Jikan API by MAL ID.

    Detailed Use:
        Queries api.jikan.moe/v4/anime/{mal_id}/episodes. If Jikan
        returns an empty list, synthesizes episodes 1..N based on the
        total episode count from the anime details.

    Need:
        Populates the episode selection panel for anime resolved via
        Jikan. Some anime have no episode data on MAL, requiring
        synthetic episode generation.

    Args:
        mal_id (str|int): The MyAnimeList ID.

    Returns:
        list[dict]: Episode list with id, number, title, released, duration.
    """
    cache_key = f"jikan_episodes:{mal_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{Config.JIKAN_BASE_URL}/anime/{mal_id}/episodes"
    try:
        r = http_client.jikan.get(
            url,
            headers={"User-Agent": Config.DEFAULT_USER_AGENT},
            timeout=Config.API_TIMEOUT,
        )
        if r.status_code == 200:
            episodes_data = r.json().get("data", [])
            eps = []
            for ep in episodes_data:
                eps.append({
                    "id": ep.get("mal_id") or ep.get("number") or 1,
                    "number": ep.get("mal_id") or ep.get("number") or 1,
                    "title": ep.get("title") or f"Episode {ep.get('mal_id')}",
                    "released": True,
                    "duration": "24m",
                })

            if not eps:
                # Synthesize episode list from total count
                info = scrape_anime_info_jikan(mal_id)
                total_episodes = info.get("episodes") or 1
                for i in range(1, total_episodes + 1):
                    eps.append({
                        "id": i,
                        "number": i,
                        "title": f"Episode {i}",
                        "released": True,
                        "duration": info.get("duration") or "24m",
                    })
            cache.set(cache_key, eps, timeout=Config.CACHE_TTL_JIKAN_EPISODES)
            return eps
    except Exception as e:
        print("Error fetching Jikan episodes:", e)

    return []
