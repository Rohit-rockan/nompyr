# ==============================================================================
# SERVICES — High-Level Metadata Enrichment Orchestration
# ==============================================================================
# Purpose:
#     Orchestrates the enrichment of anime detail pages and home feeds
#     by combining AniList metadata lookups with existing scraper data.
#     This is the "glue" layer between AniList/Jikan services and the
#     route handlers.
#
# Need:
#     Multiple routes (home, detail, search) need the same enrichment
#     logic but with slightly different parameters. This service
#     centralizes that logic to avoid duplication across route files.
# ==============================================================================

from content_service.metadata.anilist import get_anilist_metadata, get_anilist_metadata_batch, enrich_results


def enrich_detail_page(res, source):
    """
    Enrich an anime detail page response with AniList metadata.

    Detailed Use:
        Takes a raw scraper response dict and overlays it with AniList
        data: poster (replacing broken/hanime CDN images), score, trailer
        URL, format, status, genres, studio, year, and schedule. Only
        overwrites fields that are missing or contain placeholder values.

    Need:
        Scraper detail pages often lack poster images (or use hanime CDN
        URLs that trigger CORS errors), have no score, and miss studio
        or schedule info. This function fills those gaps with verified
        AniList data.

    Args:
        res (dict): The scraper's anime detail response.
        source (str): The provider name (e.g., 'animekai', 'hanime').

    Returns:
        dict: The enriched response (modified in-place).
    """
    if not isinstance(res, dict) or "error" in res:
        return res

    # Clean pipe-prefixed values
    for key in list(res.keys()):
        if isinstance(res[key], str):
            res[key] = res[key].lstrip("|").strip()
    if "detail" in res and isinstance(res["detail"], dict):
        for k, v in list(res["detail"].items()):
            if isinstance(v, str):
                res["detail"][k] = v.lstrip("|").strip()

    poster = res.get("poster", "")
    score = res.get("mal_score") or res.get("score") or "N/A"

    is_hanime = False
    if source == "hanime":
        is_hanime = True
    if poster and (
        "hanime-cdn.com" in poster
        or "hanime.tv" in poster
        or "htv-services.com" in poster
    ):
        is_hanime = True

    meta = get_anilist_metadata(res.get("title", ""))
    if meta:
        # 1. Enrich poster/banner
        is_orig_hanime = False
        if poster and (
            "hanime-cdn.com" in poster
            or "hanime.tv" in poster
            or "htv-services.com" in poster
        ):
            is_orig_hanime = True
        if meta.get("poster") and (
            not poster
            or "animeverse.to/i/" in poster
            or "nekkoto" in poster
            or is_orig_hanime
        ):
            res["poster"] = meta["poster"]
            res["banner"] = meta.get("banner") or meta["poster"]

        # 2. Enrich score
        if meta.get("score") and meta["score"] != "N/A" and (score == "N/A" or not score):
            score = meta["score"]
            if "detail" in res and isinstance(res["detail"], dict):
                res["detail"]["score"] = meta["score"]

        # 3. Enrich trailer
        if meta.get("trailer_url") and ("trailer_url" not in res or not res["trailer_url"]):
            res["trailer_url"] = meta["trailer_url"]

        # 4. Enrich metadata fields (only overwrite missing/placeholder values)
        if "type" not in res or not res["type"] or (res["type"] == "TV" and meta.get("type")):
            res["type"] = meta.get("type")
        if "status" not in res or not res["status"] or res["status"] in ("Unknown", "TBA"):
            res["status"] = meta.get("status")
        if "genres" not in res or not res["genres"] or len(res["genres"]) == 0:
            res["genres"] = meta.get("genres")
        if "studio" not in res or not res["studio"] or res["studio"] in ("Unknown Studio", "Unknown"):
            res["studio"] = meta.get("studio")
        if "year" not in res or not res["year"] or res["year"] in ("TBA", 2026):
            res["year"] = meta.get("year")
        if "schedule" not in res or not res["schedule"] or res["schedule"] == "TBA":
            res["schedule"] = meta.get("schedule")

    if score and score != "N/A":
        res["score"] = score
        res["mal_score"] = score

    return res


def prefetch_home_metadata(res):
    """
    Batch-prefetch AniList metadata for all items in a home feed response.

    Detailed Use:
        Collects all anime items across home feed sections (banner,
        latest_updates, popular, upcoming, top_trending), identifies
        those needing metadata enrichment (missing poster/score), and
        dispatches a single batch prefetch to warm the cache. Then
        enriches each section in-place.

    Need:
        Without prefetching, each card on the homepage would trigger
        an individual AniList query on render — causing hundreds of
        sequential API calls and massive latency. Batch prefetching
        resolves all metadata in 2-3 HTTP requests.

    Args:
        res (dict): The aggregated home feed response dict with keys
                    like 'banner', 'latest_updates', 'popular', etc.

    Returns:
        dict: The enriched home feed response (modified in-place).
    """
    if not isinstance(res, dict):
        return res

    # Collect all items across all sections
    all_items = []
    for section_key in ("banner", "latest_updates", "popular", "upcoming"):
        if section_key in res and res[section_key]:
            all_items.extend(res[section_key])
    if "top_trending" in res and isinstance(res["top_trending"], dict):
        for key in res["top_trending"]:
            if res["top_trending"][key]:
                all_items.extend(res["top_trending"][key])

    # Identify titles needing enrichment
    titles_to_prefetch = []
    for item in all_items:
        if not isinstance(item, dict):
            continue
        poster = item.get("poster", "")
        score = item.get("score") or item.get("mal_score") or "N/A"

        needs_enrich = False
        if score == "N/A" or not score:
            needs_enrich = True
        if not poster or "animeverse.to/i/" in poster or "nekkoto" in poster:
            needs_enrich = True

        if needs_enrich:
            title = item.get("title", "")
            if title and title not in titles_to_prefetch:
                titles_to_prefetch.append(title)

    # Batch prefetch (warms the cache for subsequent enrich_results calls)
    if titles_to_prefetch:
        get_anilist_metadata_batch(titles_to_prefetch)

    # Enrich each section
    for section_key in ("banner", "latest_updates", "popular", "upcoming"):
        if section_key in res:
            res[section_key] = enrich_results(res[section_key])
    if "top_trending" in res and isinstance(res["top_trending"], dict):
        for key in res["top_trending"]:
            res["top_trending"][key] = enrich_results(res["top_trending"][key])

    return res
