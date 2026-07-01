# ==============================================================================
# ROUTES — Search, Most-Searched, and Search Predictions
# ==============================================================================
# Purpose:
#     Blueprint for search-related routes: multi-source keyword search
#     with filters/sorting, trending keywords, and autocomplete predictions.
#
# Need:
#     Search is the primary discovery mechanism. It must aggregate results
#     from all providers, apply user filters (genre, type, status, year,
#     language, etc.), sort by various criteria, and enrich metadata.
# ==============================================================================

from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, request
import requests as _requests

from config import Config
from core import cache
from core.helpers import (
    safe_run,
    prefix_item,
    merge_lists,
    get_score_val,
    get_year_val,
    matches_language,
    matches_genre,
    matches_date_range,
)
from services.anilist import enrich_results
from scrapers import (
    search_anime,
    search_anime_aniwatch,
    search_anime_hanime,
    search_anime_miruro,
    search_anime_animenexus,
    search_anikototv,
    search_mkissa,
    search_anineko,
    search_anidb,
    scrape_most_searched,
)

search_bp = Blueprint("search", __name__)


@search_bp.route("/api/most-searched", methods=["GET"])
def api_most_searched_endpoint():
    """
    Trending search keywords route.

    Detailed Use:
        Retrieves the trending search keywords representing popular
        current searches from AnimeKai.

    Need:
        Displays search recommendations on the home search layout to
        help users see what's trending.
    """
    cached = cache.get("most_searched")
    if cached is not None:
        return jsonify(cached)

    res = scrape_most_searched()
    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]

    response_data = {"success": True, "count": len(res), "results": res}
    if "error" not in response_data:
        cache.set("most_searched", response_data, timeout=Config.CACHE_TTL_MOST_SEARCHED)
    return jsonify(response_data)


@search_bp.route("/api/search-predictions", methods=["GET"])
def api_search_predictions():
    """
    Search autocomplete predictions route.

    Detailed Use:
        Retrieves search predictions and autocomplete suggestions from
        the Jikan API based on the user's current partial input query.

    Need:
        Powers the topbar interactive autocomplete dropdown list as the
        user types.
    """
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])

    cache_key = f"predictions:{q.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    headers = {"User-Agent": Config.DEFAULT_USER_AGENT}

    try:
        url = Config.JIKAN_BASE_URL + "/anime"
        r = _requests.get(url, params={"q": q, "limit": 6}, headers=headers, timeout=Config.API_TIMEOUT)
        if r.status_code == 200:
            results = []
            for item in r.json().get("data", []):
                title = item.get("title")
                poster = (
                    item.get("images", {}).get("jpg", {}).get("small_image_url")
                    or item.get("images", {}).get("jpg", {}).get("image_url")
                    or ""
                )
                results.append({
                    "title": title,
                    "poster": poster,
                    "id": f"jikan:{item.get('mal_id')}",
                })
            if results:
                cache.set(cache_key, results, timeout=Config.CACHE_TTL_PREDICTIONS)
                return jsonify(results)
    except Exception as e:
        print("Error fetching predictions from Jikan:", e)

    return jsonify([])


@search_bp.route("/api/search", methods=["GET"])
def api_search():
    """
    Multi-source search with advanced filtering and sorting.

    Detailed Use:
        Parses keyword, page, source, and filter parameters from the query
        string. Dispatches parallel searches across providers, merges
        results, applies client-side filters (genre, type, status, year,
        rating, score, season, language, date range, multi-genres), sorts
        by the requested criterion, and enriches metadata via AniList.

    Need:
        The primary search endpoint powering the library search page.
        Must handle all filter combinations and return enriched results.
    """
    kw = request.args.get("keyword", "").strip()
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    source = request.args.get("source", "").strip().lower()

    genre = request.args.get("genre", "").strip().lower()
    atype = request.args.get("type", "").strip().lower()
    status = request.args.get("status", "").strip().lower()
    year = request.args.get("year", "").strip().lower()
    rating = request.args.get("rating", "").strip().lower()
    score = request.args.get("score", "").strip().lower()
    season = request.args.get("season", "").strip().lower()
    language = request.args.get("language", "").strip().lower()
    start_year = request.args.get("start_year", "").strip().lower()
    start_month = request.args.get("start_month", "").strip().lower()
    start_day = request.args.get("start_day", "").strip().lower()
    end_year = request.args.get("end_year", "").strip().lower()
    end_month = request.args.get("end_month", "").strip().lower()
    end_day = request.args.get("end_day", "").strip().lower()
    sort = request.args.get("sort", "").strip().lower()
    genres = request.args.get("genres", "").strip().lower()

    # Create search cache key
    cache_key = (
        f"search:{kw}:{page}:{source}:{genre}:{atype}:{status}:{year}:"
        f"{rating}:{score}:{season}:{language}:{start_year}:{start_month}:"
        f"{start_day}:{end_year}:{end_month}:{end_day}:{sort}:{genres}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    if source == "animekai":
        res = search_anime(kw, page)
    elif source == "aniwatch":
        res = search_anime_aniwatch(kw, page)
    elif source == "hanime":
        res = search_anime_hanime(kw, page)
    elif source == "miruro":
        res = search_anime_miruro(kw, page)
    elif source == "animenexus":
        res = search_anime_animenexus(kw, page)
    elif source == "anikototv":
        res = search_anikototv(kw, page)
    elif source == "mkissa":
        res = search_mkissa(kw)
    elif source == "anineko":
        res = search_anineko(kw, page)
    elif source == "all" or not source:
        with ThreadPoolExecutor(max_workers=Config.MAX_SCRAPER_WORKERS) as executor:
            fut_kai = executor.submit(safe_run, search_anime, kw, page)
            fut_watch = executor.submit(safe_run, search_anime_aniwatch, kw, page)
            fut_hanime = executor.submit(safe_run, search_anime_hanime, kw, page)
            fut_miruro = executor.submit(safe_run, search_anime_miruro, kw, page)
            fut_nexus = executor.submit(safe_run, search_anime_animenexus, kw, page)
            fut_anikototv = executor.submit(safe_run, search_anikototv, kw)
            fut_mkissa = executor.submit(safe_run, search_mkissa, kw)
            fut_anineko = executor.submit(safe_run, search_anineko, kw)
            fut_anidb = executor.submit(safe_run, search_anidb, kw)
            fut_senshi = executor.submit(safe_run, search_senshi, kw)
            fut_animotv = executor.submit(safe_run, search_animotvslash, kw)
            fut_animedekho = executor.submit(safe_run, search_animedekho, kw)

            res_kai = fut_kai.result()
            res_watch = fut_watch.result()
            res_hanime = fut_hanime.result()
            res_miruro = fut_miruro.result()
            res_nexus = fut_nexus.result()
            res_anikototv = fut_anikototv.result()
            res_mkissa = fut_mkissa.result()
            res_anineko = fut_anineko.result()
            res_anidb = fut_anidb.result()
            res_senshi = fut_senshi.result()
            res_animotv = fut_animotv.result()
            res_animedekho = fut_animedekho.result()

        def clean_res(r):
            if isinstance(r, tuple):
                return {}
            if isinstance(r, dict) and "error" in r:
                return {}
            return r or {}

        kai = clean_res(res_kai)
        watch = clean_res(res_watch)
        hanime = clean_res(res_hanime)
        miruro = clean_res(res_miruro)
        nexus = clean_res(res_nexus)
        anikototv = clean_res(res_anikototv)
        mkissa = clean_res(res_mkissa)
        anineko = clean_res(res_anineko)
        anidb = clean_res(res_anidb)
        senshi = clean_res(res_senshi)
        animotv = clean_res(res_animotv)
        animedekho = clean_res(res_animedekho)

        def prefix_list(lst, prefix):
            return [prefix_item(item, prefix) for item in lst] if lst else []

        results = merge_lists(
            prefix_list(kai.get("results", []), "animekai"),
            prefix_list(watch.get("results", []), "aniwatch"),
            prefix_list(hanime.get("results", []), "hanime"),
            prefix_list(miruro.get("results", []), "miruro"),
            prefix_list(nexus.get("results", []), "animenexus"),
            prefix_list(anikototv if isinstance(anikototv, list) else [], "anikototv"),
            prefix_list(mkissa if isinstance(mkissa, list) else [], "mkissa"),
            prefix_list(anineko if isinstance(anineko, list) else [], "anineko"),
            prefix_list(anidb if isinstance(anidb, list) else [], "anidb"),
            prefix_list(senshi if isinstance(senshi, list) else [], "senshi"),
            prefix_list(animotv if isinstance(animotv, list) else [], "animotvslash"),
            prefix_list(animedekho if isinstance(animedekho, list) else [], "animedekho"),
        )

        total = (
            (kai.get("total", 0) or 0)
            + (watch.get("total", 0) or 0)
            + (hanime.get("total", 0) or 0)
            + (miruro.get("total", 0) or 0)
            + (nexus.get("total", 0) or 0)
        )

        res = {
            "results": results,
            "total": total,
            "page": page,
            "per_page": len(results),
        }
    else:
        res = search_anime(kw, page)

    if isinstance(res, dict) and "results" in res:
        results = res["results"]
        if genre:
            results = [
                item for item in results
                if genre in str(item.get("genres", [])).lower()
                or genre in str(item.get("type", "")).lower()
                or genre in str(item.get("title", "")).lower()
                or genre in str(item.get("japanese_title", "")).lower()
                or genre in str(item.get("slug", "")).lower()
            ]
        if atype:
            results = [item for item in results if atype in str(item.get("type", "")).lower()]
        if status:
            results = [item for item in results if status in str(item.get("status", "")).lower()]
        if year:
            results = [item for item in results if year in str(item.get("year", "")).lower()]
        if rating:
            results = [
                item for item in results
                if rating in str(item.get("rating", "")).lower()
                or rating in str(item.get("ratingLabel", "")).lower()
            ]
        if score:
            try:
                min_score = float(score)
                results = [item for item in results if get_score_val(item) >= min_score]
            except ValueError:
                pass
        if season:
            results = [
                item for item in results
                if season in str(item.get("season", "")).lower()
                or season in str(item.get("premiered", "")).lower()
                or season in str(item.get("release", "")).lower()
            ]
        if language:
            results = [item for item in results if matches_language(item, language)]
        if start_year or end_year or start_month or end_month or start_day or end_day:
            results = [
                item for item in results
                if matches_date_range(item, start_year, start_month, start_day, end_year, end_month, end_day)
            ]
        if genres:
            genre_list = [g.strip().lower() for g in genres.split(",") if g.strip()]
            for g in genre_list:
                results = [item for item in results if matches_genre(item, g)]

        if sort:
            if sort == "title_asc":
                results.sort(key=lambda x: str(x.get("title", "")).lower())
            elif sort == "title_desc":
                results.sort(key=lambda x: str(x.get("title", "")).lower(), reverse=True)
            elif sort == "score_desc":
                results.sort(key=get_score_val, reverse=True)
            elif sort == "year_desc":
                results.sort(key=lambda x: get_year_val(x), reverse=True)
            elif sort == "year_asc":
                results.sort(key=lambda x: get_year_val(x))
            elif sort == "latest_desc":
                results.sort(
                    key=lambda x: str(x.get("updatedAt", "") or x.get("updated", "")),
                    reverse=True,
                )

        res["results"] = enrich_results(results)
        res["total"] = len(res["results"])
        res["per_page"] = len(res["results"])

    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]

    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_SEARCH)
    return jsonify(final_res)
