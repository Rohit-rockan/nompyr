# ==============================================================================
# ROUTES — HLS, Media, Image & Player Proxies
# ==============================================================================
# Purpose:
#     Blueprint for all proxy routes: HLS manifest rewriting, binary
#     media segment streaming, image hotlink bypass, and Hanime player
#     HTML proxy.
#
# Need:
#     External providers enforce strict CORS, referer, and hotlinking
#     policies. These proxy routes serve content through our own origin,
#     bypassing those restrictions so the frontend player works.
# ==============================================================================

from urllib.parse import quote

from flask import Blueprint, Response, request, current_app
import requests as _requests

from config import Config
from core.helpers import get_base_origin, get_proxy_session

proxy_bp = Blueprint("proxy", __name__)


@proxy_bp.route("/api/proxy-image", methods=["GET"])
def proxy_image():
    """
    Image hotlink proxy route.

    Detailed Use:
        Proxies image asset requests from external providers by passing
        referer headers (e.g., Referer: hanime.tv) in the outgoing
        request.

    Need:
        Bypasses strict hotlinking restrictions and referer/CORS blocks
        set by media providers so thumbnails render properly in client
        browsers.
    """
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400

    headers = {
        "User-Agent": Config.DEFAULT_USER_AGENT,
        "Referer": "https://hanime.tv/",
    }

    try:
        r = _requests.get(url, headers=headers, stream=True, timeout=Config.SCRAPER_TIMEOUT)
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "image/jpeg")

        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk

        return Response(generate(), content_type=content_type)
    except Exception as e:
        return f"Error fetching image: {str(e)}", 500


@proxy_bp.route("/api/proxy-hls", methods=["GET"])
@proxy_bp.route("/api/proxy-hls/stream.m3u8", methods=["GET"])
def proxy_hls():
    """
    HLS manifest rewriting proxy route.

    Detailed Use:
        Fetches an HLS .m3u8 playlist, rewrites all segment/sub-playlist
        URLs to point through this proxy (preserving referer), and streams
        binary media segments directly.

    Need:
        HLS streams from external providers are referer-locked. This
        proxy transparently rewrites the manifest so the browser's
        MediaSource API can play the content through our origin.
    """
    url = request.args.get("url")
    referer = request.args.get("referer")
    if not url:
        return "Missing url parameter", 400

    headers = {"User-Agent": Config.DEFAULT_USER_AGENT}
    if referer:
        base_ref = get_base_origin(referer)
        if base_ref:
            headers["Referer"] = base_ref

    is_playlist = url.split("?")[0].endswith(".m3u8") or ".m3u8" in url.lower()

    try:
        if is_playlist:
            session = get_proxy_session(url, headers)
            r = session.get(url, headers=headers, timeout=Config.API_TIMEOUT)
            if r.status_code != 200:
                return f"Proxy error: status {r.status_code}", r.status_code

            content = r.text
            base_url = url.rsplit("/", 1)[0] + "/"

            lines = content.splitlines()
            new_lines = []
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("#"):
                    new_lines.append(line)
                else:
                    if not line_str.startswith("http://") and not line_str.startswith("https://"):
                        resolved_url = base_url + line_str
                    else:
                        resolved_url = line_str

                    is_line_playlist = (
                        resolved_url.split("?")[0].endswith(".m3u8")
                        or ".m3u8" in resolved_url.lower()
                    )
                    path_suffix = "/stream.m3u8" if is_line_playlist else ""
                    proxied_url = f"{request.host_url}api/proxy-hls{path_suffix}?url={quote(resolved_url)}"
                    if referer:
                        proxied_url += f"&referer={quote(referer)}"
                    new_lines.append(proxied_url)

            rewritten_m3u8 = "\n".join(new_lines)
            response = current_app.response_class(
                response=rewritten_m3u8,
                status=200,
                mimetype="application/vnd.apple.mpegurl",
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
        else:
            # Proxy binary media segment (.ts or others)
            session = get_proxy_session(url, headers)
            r = session.get(url, headers=headers, stream=True, timeout=Config.SCRAPER_TIMEOUT)
            if r.status_code != 200:
                return f"Segment Proxy error: status {r.status_code}", r.status_code

            def generate_bytes():
                for chunk in r.iter_content(chunk_size=40960):
                    yield chunk

            response = current_app.response_class(
                response=generate_bytes(),
                status=200,
                mimetype=r.headers.get("Content-Type", "video/MP2T"),
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

    except Exception as e:
        return f"Proxy exception: {e}", 500


@proxy_bp.route("/api/proxy-media", methods=["GET"])
def proxy_media():
    """
    Binary media proxy with Range header support.

    Detailed Use:
        Proxies binary media requests (MP4, WebM, etc.) with full HTTP
        Range header passthrough for seeking support.

    Need:
        Enables video seeking and partial content delivery for MP4
        streams from providers with referer restrictions.
    """
    url = request.args.get("url")
    referer = request.args.get("referer")
    if not url:
        return "Missing url parameter", 400

    headers = {"User-Agent": Config.DEFAULT_USER_AGENT}
    if referer:
        base_ref = get_base_origin(referer)
        if base_ref:
            headers["Referer"] = base_ref

    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    try:
        session = get_proxy_session(url, headers)
        r = session.get(url, headers=headers, stream=True, timeout=Config.PROXY_TIMEOUT)

        def generate():
            for chunk in r.iter_content(chunk_size=40960):
                yield chunk

        response = Response(generate(), status=r.status_code, mimetype=r.headers.get("Content-Type"))

        for h in ["Content-Range", "Content-Length", "Accept-Ranges"]:
            if h in r.headers:
                response.headers[h] = r.headers[h]

        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        return f"Proxy error: {e}", 500


@proxy_bp.route("/api/proxy-player", methods=["GET"])
def proxy_player():
    """
    Hanime player HTML proxy.

    Detailed Use:
        Fetches the Hanime player page, rewrites relative asset URLs
        to absolute URLs, and serves the HTML without CSP or
        X-Frame-Options headers.

    Need:
        Enables embedding the Hanime player in our frontend by stripping
        security headers that would otherwise block iframe loading.
    """
    headers = {
        "User-Agent": Config.DEFAULT_USER_AGENT,
        "Referer": "https://hanime.tv/",
    }
    try:
        r = _requests.get("https://player.hanime.tv/", headers=headers, timeout=Config.API_TIMEOUT)
        if r.status_code != 200:
            return f"Proxy error: status {r.status_code}", r.status_code

        html = r.text
        # Rewrite relative assets to absolute URLs pointing to player.hanime.tv
        html = html.replace('src="/', 'src="https://player.hanime.tv/')
        html = html.replace('href="/', 'href="https://player.hanime.tv/')
        html = html.replace('src="js/', 'src="https://player.hanime.tv/js/')
        html = html.replace('href="js/', 'href="https://player.hanime.tv/js/')
        html = html.replace('href="css/', 'href="https://player.hanime.tv/css/')
        html = html.replace('href="fonts/', 'href="https://player.hanime.tv/fonts/')
        html = html.replace('src="img/', 'src="https://player.hanime.tv/img/')

        response = current_app.response_class(
            response=html,
            status=200,
            mimetype="text/html",
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        # This proxy has no Content-Security-Policy or X-Frame-Options,
        # permitting local embedding
        return response
    except Exception as e:
        return f"Proxy exception: {e}", 500
