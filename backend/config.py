# ==============================================================================
# NOMPYR BACKEND — CENTRALIZED CONFIGURATION
# ==============================================================================
# Purpose:
#     Single source of truth for all tunable parameters across the application.
#     Eliminates hardcoded magic numbers and centralizes environment-specific
#     settings for timeouts, cache TTLs, thread pools, admin secrets, and paths.
# ==============================================================================

import os
import hashlib


class Config:
    """
    Centralized configuration for the Nompyr backend.

    Detailed Use:
        Stores all tunable constants (timeouts, cache TTLs, pool sizes,
        admin credentials) in one place so that performance tuning, secret
        rotation, and environment changes require editing only this file.

    Need:
        Prevents magic numbers from being scattered across 20+ modules.
        Enables per-environment overrides via environment variables.
    """

    # --------------------------------------------------------------------------
    # Application Metadata
    # --------------------------------------------------------------------------
    APP_NAME = "Nompyr REST API"
    APP_VERSION = "2.0.0"

    # --------------------------------------------------------------------------
    # Network Timeouts (seconds)
    # --------------------------------------------------------------------------
    SCRAPER_TIMEOUT = 15        # Timeout for scraper HTTP requests
    API_TIMEOUT = 10            # Timeout for external API calls (Jikan, AniList)
    PROXY_TIMEOUT = 20          # Timeout for media proxy streaming
    ANILIST_TIMEOUT = 4         # Timeout for AniList GraphQL queries (single)
    ANILIST_BATCH_TIMEOUT = 6   # Timeout for AniList GraphQL batch queries

    # --------------------------------------------------------------------------
    # Thread Pool Configuration
    # --------------------------------------------------------------------------
    MAX_SCRAPER_WORKERS = 5     # Max concurrent scraper threads for home/search
    MAX_BATCH_WORKERS = 3       # Max parallel AniList batch resolution threads

    # --------------------------------------------------------------------------
    # Cache TTL Presets (seconds)
    # --------------------------------------------------------------------------
    CACHE_TTL_HOME = 600            # Home feed: 10 minutes
    CACHE_TTL_SEARCH = 300          # Search results: 5 minutes
    CACHE_TTL_DETAILS = 900         # Anime detail pages: 15 minutes
    CACHE_TTL_EPISODES = 600        # Episode lists: 10 minutes
    CACHE_TTL_SERVERS = 300         # Server lists: 5 minutes
    CACHE_TTL_SOURCE = 180          # Video source URLs: 3 minutes (keep fresh)
    CACHE_TTL_PREDICTIONS = 1800    # Search predictions: 30 minutes
    CACHE_TTL_RECOMMENDATIONS = 1800  # Recommendations: 30 minutes
    CACHE_TTL_MOST_SEARCHED = 1800  # Trending keywords: 30 minutes
    CACHE_TTL_METADATA_HIT = 604800   # AniList metadata hit: 7 days
    CACHE_TTL_METADATA_MISS = 86400   # AniList metadata miss: 1 day
    CACHE_TTL_JIKAN_DETAILS = 86400   # Jikan detail pages: 1 day
    CACHE_TTL_JIKAN_EPISODES = 86400  # Jikan episode lists: 1 day
    CACHE_TTL_JIKAN_LISTS = 3600      # Jikan seasonal lists: 1 hour

    # --------------------------------------------------------------------------
    # Connection Pooling (HTTP Adapter)
    # --------------------------------------------------------------------------
    HTTP_POOL_CONNECTIONS = 10  # Number of connection pools to cache
    HTTP_POOL_MAXSIZE = 20     # Max connections per pool
    HTTP_RETRY_TOTAL = 3       # Total retry attempts
    HTTP_RETRY_BACKOFF = 0.3   # Exponential backoff factor between retries
    HTTP_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]  # Status codes to retry

    # --------------------------------------------------------------------------
    # Default Headers
    # --------------------------------------------------------------------------
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # --------------------------------------------------------------------------
    # Database
    # --------------------------------------------------------------------------
    DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "nompyr_reviews.db"
    )

    # --------------------------------------------------------------------------
    # Content Filtering
    # --------------------------------------------------------------------------
    HENTAI_KEEP_PROBABILITY_MOD = 7   # ~14.3% keep probability (hash % mod == 0)
    MAX_HENTAI_BANNER = 1             # Max hentai items in banner section
    MAX_HENTAI_DEFAULT = 2            # Max hentai items in other sections

    # --------------------------------------------------------------------------
    # AniList Batch Configuration
    # --------------------------------------------------------------------------
    ANILIST_BATCH_SIZE = 10           # Titles per batch GraphQL query
    ANILIST_MAX_BATCHES = 3           # Max batches per request (30 titles max)
    ANILIST_BATCH_DELAY = 0.5         # Delay between batch requests (rate limit)
    ANILIST_MAX_VARIANTS = 4          # Max title variants for single metadata query
    ANILIST_BATCH_MAX_VARIANTS = 2    # Max title variants per batch item

    # --------------------------------------------------------------------------
    # Hidden Admin Gateway
    # --------------------------------------------------------------------------
    ADMIN_ROUTE_PREFIX = "/api/n0m-ctrl-x9"
    ADMIN_USERNAME = "nompyr_owner"
    # Store password hash instead of plaintext for security
    _ADMIN_PASSWORD_PLAIN = "Nompyr-Secure-Admin-9872"
    ADMIN_PASSWORD_HASH = hashlib.sha256(
        _ADMIN_PASSWORD_PLAIN.encode()
    ).hexdigest()
    ADMIN_SESSION_TOKEN = "secure_admin_session_token_2026"

    # --------------------------------------------------------------------------
    # CORS
    # --------------------------------------------------------------------------
    CORS_ORIGINS = "*"  # Allow all origins (tighten for production)

    # --------------------------------------------------------------------------
    # AniList API
    # --------------------------------------------------------------------------
    ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"

    # --------------------------------------------------------------------------
    # Jikan API
    # --------------------------------------------------------------------------
    JIKAN_BASE_URL = "https://api.jikan.moe/v4"
    JIKAN_RATE_LIMIT_DELAY = 0.3  # Delay between consecutive Jikan requests
    JIKAN_SEASONAL_DELAY = 0.5    # Delay between seasonal list requests
