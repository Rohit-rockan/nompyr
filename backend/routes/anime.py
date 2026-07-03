# ==============================================================================
# ROUTES — Anime Details, Episodes & Servers
# ==============================================================================
# Purpose:
#     Blueprint for anime detail resolution, episode listing, and server
#     listing routes. Handles multi-provider dispatch, source prefix
#     parsing, fallback pages, and metadata enrichment.
#
# Need:
#     These routes power the anime detail page, episode selector, and
#     server picker — the core content consumption flow after discovery.
# ==============================================================================

from urllib.parse import unquote

from flask import Blueprint, jsonify, request

from config import Config
from core import cache
from services.enrichment import enrich_detail_page
from services.jikan import scrape_anime_info_jikan, fetch_episodes_jikan
from scrapers import (
    scrape_anime_info,
    scrape_anime_info_aniwatch,
    scrape_anime_info_hanime,
    scrape_anime_info_miruro,
    scrape_anime_info_animenexus,
    fetch_episodes,
    fetch_episodes_aniwatch,
    fetch_episodes_hanime,
    fetch_episodes_miruro,
    fetch_episodes_animenexus,
    fetch_servers,
    fetch_servers_aniwatch,
    fetch_servers_hanime,
    fetch_servers_miruro,
    fetch_servers_animenexus,
    scrape_anime_info_anikototv,
    fetch_episodes_anikototv,
    fetch_servers_anikototv,
    scrape_anime_info_mkissa,
    fetch_episodes_mkissa,
    fetch_servers_mkissa,
    scrape_anime_info_anineko,
    fetch_episodes_anineko,
    fetch_servers_anineko,
    scrape_anime_info_anidb,
    fetch_episodes_anidb,
    fetch_servers_anidb,
    scrape_anime_info_senshi,
    fetch_episodes_senshi,
    fetch_servers_senshi,
    scrape_anime_info_animotvslash,
    fetch_episodes_animotvslash,
    fetch_servers_animotvslash,
    scrape_anime_info_animedekho,
    fetch_episodes_animedekho,
    fetch_servers_animedekho,
)

anime_bp = Blueprint("anime", __name__)


# ------------------------------------------------------------------------------
# Helper: Parse source prefix from a prefixed identifier
# ------------------------------------------------------------------------------
_SOURCE_PREFIXES = ("hanime:", "aniwatch:", "animekai:", "miruro:", "animenexus:", "jikan:", "anikototv:", "mkissa:", "anineko:", "anidb:")


def _parse_source_prefix(identifier):
    """
    Parse source prefix from a provider-prefixed identifier.

    Returns:
        tuple: (source_name, stripped_identifier)
    """
    for prefix in _SOURCE_PREFIXES:
        if identifier.startswith(prefix):
            return prefix.rstrip(":"), identifier.split(prefix, 1)[1]
    return None, identifier


@anime_bp.route("/api/anime/<slug>", methods=["GET"])
def api_anime_info(slug):
    """
    Anime detail page route.

    Detailed Use:
        Parses the provider prefix from the slug, dispatches to the
        appropriate scraper, falls back to a generated detail page on
        error, enriches metadata via AniList, and caches the result.

    Need:
        Powers the anime detail page with title, poster, banner, score,
        trailer, genres, studio, status, year, and schedule info.
    """
    slug = unquote(slug)
    cache_key = f"anime:{slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    source, stripped_slug = _parse_source_prefix(slug)
    if source is None:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"

    if source == "aniwatch":
        res = scrape_anime_info_aniwatch(stripped_slug)
    elif source == "hanime":
        res = scrape_anime_info_hanime(stripped_slug)
    elif source == "miruro":
        res = scrape_anime_info_miruro(stripped_slug)
    elif source == "animenexus":
        res = scrape_anime_info_animenexus(stripped_slug)
    elif source == "anikototv":
        res = scrape_anime_info_anikototv(stripped_slug)
    elif source == "mkissa":
        res = scrape_anime_info_mkissa(stripped_slug)
    elif source == "anineko":
        res = scrape_anime_info_anineko(stripped_slug)
    elif source == "anidb":
        res = scrape_anime_info_anidb(stripped_slug)
    elif source == "senshi":
        res = scrape_anime_info_senshi(stripped_slug)
    elif source == "animotvslash":
        res = scrape_anime_info_animotvslash(stripped_slug)
    elif source == "animedekho":
        res = scrape_anime_info_animedekho(stripped_slug)
    elif source == "jikan":
        res = scrape_anime_info_jikan(stripped_slug)
    else:
        res = scrape_anime_info(stripped_slug)

    if isinstance(res, tuple):
        clean_title = stripped_slug.replace("-", " ").title()
        res = {
            "ani_id": f"{source}:{stripped_slug}",
            "title": clean_title,
            "japanese_title": clean_title,
            "description": (
                f"This is a fallback details page for {clean_title} parsed by the "
                f"Nompyr server because the source '{source}' returned an error."
            ),
            "poster": "https://images.unsplash.com/photo-1541562232579-512a21360020?auto=format&fit=crop&w=720&q=80",
            "banner": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1600&q=80",
            "sub_episodes": 12,
            "dub_episodes": 12,
            "type": "TV",
            "rating": "PG-13",
            "mal_score": "8.0",
            "genres": ["Action", "Adventure"],
            "studio": "Nompyr Fallback Studio",
            "status": "Ongoing",
            "year": 2026,
            "schedule": "TBA",
            "sourceHealth": f"Fallback ({source})",
            "is_fallback": True,
        }

    if isinstance(res, dict) and "ani_id" in res:
        if not str(res["ani_id"]).startswith(f"{source}:"):
            res["ani_id"] = f"{source}:{res['ani_id']}"

    if isinstance(res, dict) and "error" not in res:
        res = enrich_detail_page(res, source)

    final_res = {"success": True, **res}
    if "error" not in final_res and not final_res.get("is_fallback"):
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_DETAILS)
    return jsonify(final_res)


@anime_bp.route("/api/episodes/<ani_id>", methods=["GET"])
def api_episodes(ani_id):
    """
    Episode list route.

    Detailed Use:
        Parses the provider prefix from the ani_id, dispatches to the
        appropriate scraper, falls back to generated episodes on error,
        and prefixes episode tokens with the source name.

    Need:
        Powers the episode selector panel on the watch page.
    """
    ani_id = unquote(ani_id)
    cache_key = f"episodes:{ani_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    source, stripped_id = _parse_source_prefix(ani_id)
    if source is None:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"

    if source == "aniwatch":
        res = fetch_episodes_aniwatch(stripped_id)
    elif source == "hanime":
        res = fetch_episodes_hanime(stripped_id)
    elif source == "miruro":
        res = fetch_episodes_miruro(stripped_id)
    elif source == "animenexus":
        res = fetch_episodes_animenexus(stripped_id)
    elif source == "anikototv":
        res = fetch_episodes_anikototv(stripped_id)
    elif source == "mkissa":
        res = fetch_episodes_mkissa(stripped_id)
    elif source == "anineko":
        res = fetch_episodes_anineko(stripped_id)
    elif source == "anidb":
        # anidb info fetches episodes directly in the info scraper
        res = []
    elif source == "senshi":
        res = fetch_episodes_senshi(stripped_id)
    elif source == "animotvslash":
        res = fetch_episodes_animotvslash(stripped_id)
    elif source == "animedekho":
        res = fetch_episodes_animedekho(stripped_id)
    elif source == "jikan":
        res = fetch_episodes_jikan(stripped_id)
    else:
        res = fetch_episodes(stripped_id)

    if isinstance(res, tuple):
        res = []
        for i in range(1, 13):
            res.append({
                "id": f"{stripped_id}-ep-{i}",
                "number": i,
                "title": f"Episode {i}",
                "released": True,
                "duration": "24m",
            })

    if isinstance(res, list):
        prefixed_eps = []
        for ep in res:
            ep_copy = dict(ep)
            if "token" in ep_copy and ep_copy["token"]:
                if not str(ep_copy["token"]).startswith(f"{source}:"):
                    ep_copy["token"] = f"{source}:{ep_copy['token']}"
            else:
                ep_copy["token"] = f"{source}:{stripped_id}:ep-{ep_copy.get('number', '1')}"
            prefixed_eps.append(ep_copy)
        res = prefixed_eps

    final_res = {"success": True, "ani_id": ani_id, "count": len(res), "episodes": res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_EPISODES)
    return jsonify(final_res)


@anime_bp.route("/api/servers/<ep_token>", methods=["GET"])
def api_servers(ep_token):
    """
    Server list route.

    Detailed Use:
        Parses the provider prefix from the ep_token, dispatches to
        the appropriate scraper, falls back to a generated server on
        error, and prefixes server link_ids with the source name.

    Need:
        Powers the server selector dropdown on the watch page, showing
        available streaming servers for a specific episode.
    """
    ep_token = unquote(ep_token)
    cache_key = f"servers:{ep_token}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    source = None
    stripped_token = ep_token

    if ep_token.startswith("hanime:"):
        source = "hanime"
    elif ep_token.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_token = ep_token.split("aniwatch:", 1)[1]
    elif ep_token.startswith("animekai:"):
        source = "animekai"
        stripped_token = ep_token.split("animekai:", 1)[1]
    elif ep_token.startswith("mkissa:"):
        source = "mkissa"
        stripped_token = ep_token.split("mkissa:", 1)[1]
    elif ep_token.startswith("anineko:"):
        source = "anineko"
        stripped_token = ep_token.split("anineko:", 1)[1]
    elif ep_token.startswith("miruro:"):
        source = "miruro"
        stripped_token = ep_token.split("miruro:", 1)[1]
    elif ep_token.startswith("animenexus:"):
        source = "animenexus"
        stripped_token = ep_token.split("animenexus:", 1)[1]
    else:
        source = request.args.get("source", "").strip().lower()
        if not source:
            source = "animekai"

    if source == "aniwatch":
        res = fetch_servers_aniwatch(stripped_token)
    elif source == "hanime":
        res = fetch_servers_hanime(ep_token)
    elif source == "miruro":
        res = fetch_servers_miruro(ep_token)
    elif source == "animenexus":
        res = fetch_servers_animenexus(ep_token)
    elif source == "anikototv":
        res = fetch_servers_anikototv(ep_token)
    elif source == "mkissa":
        res = fetch_servers_mkissa(ep_token)
    elif source == "anineko":
        res = fetch_servers_anineko(None, ep_token)
    elif source == "anidb":
        res = fetch_servers_anidb(None, ep_token)
    elif source == "senshi":
        res = fetch_servers_senshi(ep_token)
    elif source == "animotvslash":
        res = fetch_servers_animotvslash(ep_token)
    elif source == "animedekho":
        res = fetch_servers_animedekho(ep_token)
    else:
        res = fetch_servers(stripped_token)

    if isinstance(res, tuple):
        res = {
            "servers": {
                "sub": [
                    {
                        "id": f"{stripped_token}-sub-primary",
                        "label": "Nompyr Sub",
                        "link_id": f"{stripped_token}-primary",
                        "quality": ["720p"],
                    }
                ]
            }
        }

    if isinstance(res, dict) and "servers" in res:
        for lang in res["servers"]:
            prefixed_srvs = []
            for srv in res["servers"][lang]:
                srv_copy = dict(srv)
                if "link_id" in srv_copy and srv_copy["link_id"]:
                    if not str(srv_copy["link_id"]).startswith(f"{source}:"):
                        srv_copy["link_id"] = f"{source}:{srv_copy['link_id']}"
                prefixed_srvs.append(srv_copy)
            res["servers"][lang] = prefixed_srvs

    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_SERVERS)
    return jsonify(final_res)
