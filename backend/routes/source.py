# ==============================================================================
# ROUTES — Video Source Stream Resolver
# ==============================================================================
# Purpose:
#     Blueprint for the video stream resolution route. Dispatches to
#     provider-specific extractors, rewrites stream URLs through the
#     local HLS/media proxy, and caches the result.
#
# Need:
#     Required to get playable media links dynamically on request,
#     bypassing CORS blocks using local server proxies.
# ==============================================================================

from urllib.parse import unquote, quote

from flask import Blueprint, jsonify, request

from config import Config
from core import cache
from core.helpers import get_base_origin
from scrapers import (
    resolve_source,
    resolve_miruro_source,
    resolve_animenexus_source,
    resolve_anikototv_source,
    resolve_mkissa_source,
    resolve_anineko_source,
    resolve_anidb_source,
    resolve_hanime_source,
    resolve_senshi_source,
    resolve_animotvslash_source,
    resolve_animedekho_source,
)

source_bp = Blueprint("source", __name__)


@source_bp.route("/api/source/<path:link_id>", methods=["GET"])
def api_source(link_id):
    """
    Video source stream resolver route.

    Detailed Use:
        Parses the provider source prefix from the link_id, executes
        the provider's specific extractor to fetch direct stream links,
        translates relative links to the HLS/media proxy, and caches
        the result.

    Need:
        Required to get playable media links dynamically on request,
        bypassing CORS blocks using local server proxies.
    """
    link_id = unquote(link_id)
    cache_key = f"source:{link_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    source = None
    stripped_link = link_id

    if link_id.startswith("hanime:"):
        source = "hanime"
    elif link_id.startswith("aniwatch:"):
        source = "aniwatch"
        stripped_link = link_id.split("aniwatch:", 1)[1]
    elif link_id.startswith("animekai:"):
        source = "animekai"
        stripped_link = link_id.split("animekai:", 1)[1]
    elif link_id.startswith("miruro:"):
        source = "miruro"
        stripped_link = link_id.split("miruro:", 1)[1]
    elif link_id.startswith("animenexus:"):
        source = "animenexus"
        stripped_link = link_id.split("animenexus:", 1)[1]
    elif link_id.startswith("anikototv:"):
        source = "anikototv"
        stripped_link = link_id.split("anikototv:", 1)[1]
    elif link_id.startswith("mkissa:"):
        source = "mkissa"
        stripped_link = link_id.split("mkissa:", 1)[1]
    elif link_id.startswith("anineko:"):
        source = "anineko"
        stripped_link = link_id.split("anineko:", 1)[1]
    else:
        if "hanime" in link_id:
            source = "hanime"
        elif "aniwatch" in link_id or "megaplay.buzz" in link_id or "1anime" in link_id:
            source = "aniwatch"
        elif "miruro" in link_id:
            source = "miruro"
        elif "animenexus" in link_id:
            source = "animenexus"
        elif "anikototv" in link_id:
            source = "anikototv"
        elif "mkissa" in link_id:
            source = "mkissa"
        elif "anineko" in link_id:
            source = "anineko"
        else:
            source = "animekai"

    if source == "hanime":
        res = resolve_hanime_source(link_id)
    elif source == "aniwatch":
        res = resolve_source(stripped_link)
    elif source == "miruro":
        res = resolve_miruro_source(stripped_link)
    elif source == "animenexus":
        res = resolve_animenexus_source(stripped_link)
    elif source == "anikototv":
        res = resolve_anikototv_source(stripped_link)
    elif source == "mkissa":
        res = resolve_mkissa_source(stripped_link)
    elif source == "anineko":
        res = resolve_anineko_source(stripped_link)
    elif source == "anidb":
        res = resolve_anidb_source(stripped_link)
    elif source == "senshi":
        res = resolve_senshi_source(stripped_link)
    elif source == "animotvslash":
        res = resolve_animotvslash_source(stripped_link)
    elif source == "animedekho":
        res = resolve_animedekho_source(stripped_link)
    else:
        res = resolve_source(stripped_link)

    if isinstance(res, tuple):
        res = {
            "sources": [
                {"file": "", "type": "hls", "label": "Demo fallback"}
            ],
            "message": "Demo mode stream fallback: video playback is not active for this provider.",
        }

    # Apply HLS Referrer Proxy to prevent CORS/referer blocks
    if isinstance(res, dict) and "sources" in res:
        embed_url = res.get("embed_url") or res.get("embedUrl") or ""
        new_sources = []
        for s in res["sources"]:
            if isinstance(s, dict):
                s_copy = dict(s)
                file_url = s_copy.get("file", "")
                if s_copy.get("type") == "hls" or file_url.split("?")[0].endswith(".m3u8"):
                    cleaned_ref = get_base_origin(embed_url) if embed_url else ""
                    proxied = f"{request.host_url}api/proxy-hls/stream.m3u8?url={quote(file_url)}"
                    if cleaned_ref:
                        proxied += f"&referer={quote(cleaned_ref)}"
                    s_copy["file"] = proxied
                elif (
                    s_copy.get("type") == "mp4"
                    or file_url.split("?")[0].endswith(".mp4")
                    or "stream" in file_url.lower()
                ):
                    cleaned_ref = get_base_origin(embed_url) if embed_url else ""
                    proxied = f"{request.host_url}api/proxy-media?url={quote(file_url)}"
                    if cleaned_ref:
                        proxied += f"&referer={quote(cleaned_ref)}"
                    s_copy["file"] = proxied
                new_sources.append(s_copy)
        res["sources"] = new_sources

        # Strip CSP/X-Frame-Options by proxying player.hanime.tv on our own origin
        if link_id.startswith("hanime:") and new_sources:
            proxied_hls_url = new_sources[0]["file"]
            res["embed_url"] = f"{request.host_url}api/proxy-player#{quote(proxied_hls_url)}"

    final_res = {"success": True, **res}
    if "error" not in final_res:
        cache.set(cache_key, final_res, timeout=Config.CACHE_TTL_SOURCE)
    return jsonify(final_res)
