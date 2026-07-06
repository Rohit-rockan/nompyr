# ==============================================================================
# ROUTES — Hidden Admin Gateway
# ==============================================================================
# Purpose:
#     Blueprint for the hidden admin dashboard. Provides authenticated
#     access to cache statistics, scraper health diagnostics, database
#     stats, and manual cache invalidation.
#
# Need:
#     Gives the project owner a private monitoring interface accessible
#     at a secret URL path that is not linked anywhere in the UI or
#     API index. Enables production debugging without exposing internals.
# ==============================================================================

import hashlib
import os

from flask import Blueprint, jsonify, request

from config import Config
from core import cache
from core.database import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/cache/clear", methods=["GET", "POST"])
def clear_api_cache():
    """
    Public cache invalidation route (legacy).

    Detailed Use:
        Clears all records stored in the SimpleCache instance.

    Need:
        Enables manual admin resets to invalidate cached anime details
        or search lists. Kept for backward compatibility.
    """
    cache.clear()
    return jsonify({"success": True, "message": "In-memory cache cleared successfully."})


@admin_bp.route(f"{Config.ADMIN_ROUTE_PREFIX}/auth", methods=["POST"])
def admin_auth():
    """
    Hidden admin login endpoint.

    Detailed Use:
        Validates username and password against the configured admin
        credentials (password compared via SHA-256 hash). Returns a
        session token on success.

    Need:
        Protects the admin dashboard from unauthorized access. The
        session token must be included in subsequent admin requests
        as an Authorization header.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if username == Config.ADMIN_USERNAME and password_hash == Config.ADMIN_PASSWORD_HASH:
        return jsonify({
            "success": True,
            "token": Config.ADMIN_SESSION_TOKEN,
            "message": "Admin authentication successful.",
        })

    return jsonify({"success": False, "error": "Invalid credentials"}), 401


def _verify_admin_token():
    """Verify the admin session token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    return token == Config.ADMIN_SESSION_TOKEN


@admin_bp.route(f"{Config.ADMIN_ROUTE_PREFIX}/dashboard", methods=["GET"])
def admin_dashboard():
    """
    Admin dashboard data endpoint.

    Detailed Use:
        Returns diagnostic data: cache statistics (entries, hits,
        misses, hit rate), database stats (reviews count, DB file size),
        and application configuration metadata.

    Need:
        Powers the hidden admin monitoring panel for assessing cache
        efficiency, database health, and scraper status.
    """
    if not _verify_admin_token():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # Cache statistics
    cache_stats = cache.stats()

    # Database statistics
    db_stats = {"reviews_count": 0, "db_size_bytes": 0}
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews")
        db_stats["reviews_count"] = cursor.fetchone()[0]
        cursor.execute("SELECT pg_database_size(current_database())")
        db_stats["db_size_bytes"] = cursor.fetchone()[0]
    except Exception as e:
        db_stats["error"] = str(e)

    return jsonify({
        "success": True,
        "cache": cache_stats,
        "database": db_stats,
        "config": {
            "app_name": Config.APP_NAME,
            "version": Config.APP_VERSION,
            "scraper_timeout": Config.SCRAPER_TIMEOUT,
            "max_workers": Config.MAX_SCRAPER_WORKERS,
            "cache_ttls": {
                "home": Config.CACHE_TTL_HOME,
                "search": Config.CACHE_TTL_SEARCH,
                "details": Config.CACHE_TTL_DETAILS,
                "episodes": Config.CACHE_TTL_EPISODES,
                "servers": Config.CACHE_TTL_SERVERS,
                "source": Config.CACHE_TTL_SOURCE,
            },
        },
    })


@admin_bp.route(f"{Config.ADMIN_ROUTE_PREFIX}/cache/clear", methods=["POST"])
def admin_cache_clear():
    """
    Authenticated cache clear endpoint.

    Detailed Use:
        Clears the cache after verifying the admin session token.

    Need:
        Provides a secure cache invalidation mechanism for the admin
        dashboard, separate from the public cache clear endpoint.
    """
    if not _verify_admin_token():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    cache.clear()
    return jsonify({"success": True, "message": "Cache cleared by admin."})


@admin_bp.route("/api/test-crash", methods=["GET", "POST"])
def test_crash():
    """
    Test endpoint designed to intentionally throw a ZeroDivisionError 
    so the global exception handler can catch it and send a Discord webhook 
    as 'The Mechanic' bot.
    """
    # Intentional crash for testing purposes
    x = 1 / 0
    return jsonify({"success": True})


@admin_bp.route("/api/test-librarian", methods=["GET", "POST"])
def test_librarian():
    """
    Test endpoint to manually trigger the Librarian Bot's cleanup task
    without waiting 24 hours.
    """
    from background_workers.librarian import run_librarian_cleanup
    # Run it synchronously for testing
    run_librarian_cleanup()
    return jsonify({"success": True, "message": "Librarian cleanup triggered successfully!"})
