# ==============================================================================
# ROUTES — Home Feed & API Index
# ==============================================================================
# Purpose:
#     Blueprint for the homepage feed aggregation route and the root
#     API diagnostics route. Handles multi-provider home scraping,
#     round-robin merging, content filtering, and metadata enrichment.
#
# Need:
#     The homepage is the highest-traffic route and the first impression
#     for every user. It must aggregate data from 5+ providers, filter
#     adult content, enrich metadata, and respond within 2-3 seconds.
# ==============================================================================

from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, request

from config import Config
from core import cache
from core.helpers import safe_run, prefix_item, merge_lists
from content_service.metadata.content_filter import filter_and_demote_hentai
from content_service.metadata.enrichment import prefetch_home_metadata
from scraper_service.sources import (
    scrape_home,
    scrape_home_aniwatch,
    scrape_home_hanime,
    scrape_home_miruro,
    scrape_home_animenexus,
    scrape_home_anikototv,
    scrape_home_allanime,
    scrape_home_anineko,
    scrape_home_anidb,
    scrape_home_senshi,
    scrape_home_animotvslash,
    scrape_home_animedekho,
)

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def index():
    """
    Root API diagnostics route.

    Detailed Use:
        Returns JSON describing server status, API name, current version,
        and lists available HTTP resource endpoints.

    Need:
        Provides an easy validation endpoint to verify that the Flask
        server is running and responsive.
    """
    return jsonify({
        "success": True,
        "api": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "endpoints": {
            "/api/home": "Get banner, latest updates, and trending (Cached)",
            "/api/most-searched": "Get most-searched anime keywords (Cached)",
            "/api/search?keyword=...": "Search anime (Cached)",
            "/api/anime/<slug>": "Get anime details (Cached)",
            "/api/episodes/<ani_id>": "Get episode list (Cached)",
            "/api/servers/<ep_token>": "Get available servers for an episode (Cached)",
            "/api/source/<path:link_id>": "Get direct stream sources (Cached)",
            "/api/cache/clear": "Clear in-memory cache",
        },
    })


@home_bp.route("/api/home", methods=["GET"])
def api_home():
    """
    Aggregated homepage feed route.

    Detailed Use:
        Scrapes home feeds from multiple providers in parallel, merges
        results using round-robin distribution, filters hentai content,
        prefetches AniList metadata, and enriches all items.

    Need:
        Powers the main homepage with banner, latest updates, trending,
        popular, and upcoming sections from all active providers.
    """
    source = request.args.get("source", "").strip().lower()

    cache_key = f"home:{source}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    if source == "animekai":
        res = scrape_home()
    elif source == "aniwatch":
        res = scrape_home_aniwatch()
    elif source == "hanime":
        res = scrape_home_hanime()
    elif source == "miruro":
        res = scrape_home_miruro()
    elif source == "animenexus":
        res = scrape_home_animenexus()
    elif source == "anikototv":
        res = scrape_home_anikototv()
    elif source == "allanime":
        res = scrape_home_allanime()
    elif source == "anineko":
        res = scrape_home_anineko()
    elif source == "senshi":
        res = scrape_home_senshi()
    elif source == "animotvslash":
        res = scrape_home_animotvslash()
    elif source == "animedekho":
        res = scrape_home_animedekho()
    elif source == "all" or not source:
        with ThreadPoolExecutor(max_workers=Config.MAX_SCRAPER_WORKERS) as executor:
            fut_kai = executor.submit(safe_run, scrape_home)
            fut_watch = executor.submit(safe_run, scrape_home_aniwatch)
            fut_hanime = executor.submit(safe_run, scrape_home_hanime)
            fut_miruro = executor.submit(safe_run, scrape_home_miruro)
            fut_nexus = executor.submit(safe_run, scrape_home_animenexus)
            fut_anikototv = executor.submit(safe_run, scrape_home_anikototv)
            fut_allanime = executor.submit(safe_run, scrape_home_allanime)
            fut_anineko = executor.submit(safe_run, scrape_home_anineko)
            fut_anidb = executor.submit(safe_run, scrape_home_anidb)
            fut_senshi = executor.submit(safe_run, scrape_home_senshi)
            fut_animotv = executor.submit(safe_run, scrape_home_animotvslash)
            fut_animedekho = executor.submit(safe_run, scrape_home_animedekho)

            res_kai = fut_kai.result()
            res_watch = fut_watch.result()
            res_hanime = fut_hanime.result()
            res_miruro = fut_miruro.result()
            res_nexus = fut_nexus.result()
            res_anikototv = fut_anikototv.result()
            res_allanime = fut_allanime.result()
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
        allanime = clean_res(res_allanime)
        anineko = clean_res(res_anineko)
        anidb = clean_res(res_anidb)
        senshi = clean_res(res_senshi)
        animotvslash = clean_res(res_animotv)
        animedekho = clean_res(res_animedekho)

        def prefix_list(lst, prefix):
            if not lst:
                return []
            filtered = []
            for item in lst:
                if not item.get("title") or not item.get("poster") or not item.get("ani_id"):
                    continue
                filtered.append(prefix_item(item, prefix))
            return filtered

        banners = merge_lists(
            prefix_list(kai.get("banner", []), "animekai"),
            prefix_list(watch.get("banner", []), "aniwatch"),
            prefix_list(hanime.get("banner", []), "hanime"),
            prefix_list(miruro.get("banner", []), "miruro"),
            prefix_list(nexus.get("banner", []), "animenexus"),
            prefix_list(anikototv.get("banner", []), "anikototv"),
            prefix_list(allanime.get("banner", []), "allanime"),
            prefix_list(anineko.get("banner", []), "anineko"),
            prefix_list(anidb.get("banner", []), "anidb"),
            prefix_list(senshi.get("banner", []), "senshi"),
            prefix_list(animotvslash.get("banner", []), "animotvslash"),
            prefix_list(animedekho.get("banner", []), "animedekho"),
        )

        latest = merge_lists(
            prefix_list(kai.get("latest_updates", []), "animekai"),
            prefix_list(watch.get("latest_updates", []), "aniwatch"),
            prefix_list(hanime.get("latest_updates", []), "hanime"),
            prefix_list(miruro.get("latest_updates", []), "miruro"),
            prefix_list(nexus.get("latest_updates", []), "animenexus"),
            prefix_list(anikototv.get("latest_updates", []), "anikototv"),
            prefix_list(allanime.get("latest_updates", []), "allanime"),
            prefix_list(anineko.get("latest_updates", []), "anineko"),
        )

        t_kai = kai.get("top_trending", {})
        t_watch = watch.get("top_trending", {})
        t_hanime = hanime.get("top_trending", {})
        t_miruro = miruro.get("top_trending", {})
        t_nexus = nexus.get("top_trending", {})
        t_anidb = anidb.get("top_trending", {})

        trending = {}
        for key in ["NOW", "DAY", "WEEK", "MONTH"]:
            trending[key] = merge_lists(
                prefix_list(t_kai.get(key, []), "animekai"),
                prefix_list(t_watch.get(key, []), "aniwatch"),
                prefix_list(t_hanime.get(key, []), "hanime"),
                prefix_list(t_miruro.get(key, []), "miruro"),
                prefix_list(t_nexus.get(key, []), "animenexus"),
                prefix_list(t_anidb.get(key, []), "anidb"),
            )

        popular = merge_lists(
            prefix_list(kai.get("popular", []), "animekai"),
            prefix_list(watch.get("popular", []), "aniwatch"),
            prefix_list(hanime.get("popular", []), "hanime"),
            prefix_list(miruro.get("popular", []), "miruro"),
            prefix_list(nexus.get("popular", []), "animenexus"),
            prefix_list(anidb.get("popular", []), "anidb"),
        )

        upcoming = merge_lists(
            prefix_list(kai.get("upcoming", []), "animekai"),
            prefix_list(watch.get("upcoming", []), "aniwatch"),
            prefix_list(hanime.get("upcoming", []), "hanime"),
            prefix_list(miruro.get("upcoming", []), "miruro"),
            prefix_list(nexus.get("upcoming", []), "animenexus"),
        )

        res = {
            "banner": filter_and_demote_hentai(banners, max_hentai=Config.MAX_HENTAI_BANNER),
            "latest_updates": filter_and_demote_hentai(latest, max_hentai=Config.MAX_HENTAI_DEFAULT),
            "top_trending": {
                key: filter_and_demote_hentai(val, max_hentai=Config.MAX_HENTAI_DEFAULT)
                for key, val in trending.items()
            },
            "popular": filter_and_demote_hentai(popular, max_hentai=Config.MAX_HENTAI_DEFAULT),
            "upcoming": filter_and_demote_hentai(upcoming, max_hentai=Config.MAX_HENTAI_DEFAULT),
        }
    else:
        res = scrape_home()

    if isinstance(res, tuple):
        return jsonify(res[0]), res[1]

    if isinstance(res, dict):
        res = prefetch_home_metadata(res)

    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_HOME)
    return jsonify(final_res)
