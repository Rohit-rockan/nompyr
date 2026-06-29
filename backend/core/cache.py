# ==============================================================================
# CORE — Thread-Safe In-Memory TTL Cache
# ==============================================================================
# Purpose:
#     Provides a thread-safe, key-value memory cache with per-entry TTL
#     (Time To Live) expiration. Expired keys are lazily cleaned on access.
#
# Need:
#     Reduces redundant API requests to external services (AniList, Jikan,
#     scrapers), boosting response times while respecting upstream rate limits.
#     Sits at the center of every route handler's hot path.
# ==============================================================================

import time
from threading import Lock


class SimpleCache:
    """
    Thread-safe in-memory cache with per-entry TTL expiration.

    Detailed Use:
        Stores key-value pairs mapped with expiration timestamps. On retrieval,
        expired keys are lazily deleted to free memory. All operations are
        protected by a threading Lock for safe concurrent access.

    Need:
        The primary latency optimization layer — prevents duplicate scraper
        calls and API queries by returning cached results instantly. Critical
        for surviving AniList/Jikan rate limits (429 responses).
    """

    def __init__(self):
        """Initialize empty cache storage and thread lock."""
        self._cache = {}
        self._lock = Lock()
        # --- Cache statistics for admin dashboard ---
        self._hits = 0
        self._misses = 0

    def get(self, key):
        """
        Fetch a value by key if the entry has not expired.

        Detailed Use:
            Checks if the key exists and its TTL has not elapsed. Returns the
            cached value on hit, or None on miss/expiry. Expired entries are
            deleted immediately to free memory.

        Need:
            Prevents processing duplicate scraper/API calls by returning
            cached results immediately on subsequent requests.

        Args:
            key (str): The cache key to look up.

        Returns:
            The cached value, or None if not found or expired.
        """
        with self._lock:
            if key in self._cache:
                val, expires = self._cache[key]
                if time.time() < expires:
                    self._hits += 1
                    return val
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key, value, timeout=300):
        """
        Store a value with a specific TTL timeout.

        Detailed Use:
            Inserts or updates a cache entry with the given key, value, and
            expiration window (default 5 minutes).

        Need:
            Updates the cache with fresh data while defining when it should
            be considered stale and re-fetched.

        Args:
            key (str): The cache key.
            value: The value to cache (any serializable object).
            timeout (int): Time-to-live in seconds (default: 300).
        """
        expires = time.time() + timeout
        with self._lock:
            self._cache[key] = (value, expires)

    def clear(self):
        """
        Clear all records from the cache.

        Detailed Use:
            Removes every entry from the cache dictionary and resets
            hit/miss counters.

        Need:
            Enables manually triggered cache invalidation via the admin
            dashboard or the cache clear API endpoint.
        """
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self):
        """
        Return cache statistics for the admin dashboard.

        Detailed Use:
            Provides a snapshot of current cache health: total entries,
            cumulative hit/miss counts, and hit rate percentage.

        Need:
            Powers the hidden admin dashboard's cache monitoring panel,
            allowing the owner to assess cache efficiency and decide
            whether to tune TTLs or trigger a manual clear.

        Returns:
            dict: Cache statistics including entries, hits, misses, hit_rate.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            return {
                "entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (
                    f"{(self._hits / total_requests * 100):.1f}%"
                    if total_requests > 0
                    else "N/A"
                ),
            }


# ------------------------------------------------------------------------------
# Singleton Cache Instance
# ------------------------------------------------------------------------------
# A single global cache instance shared across all modules. Import via:
#     from core.cache import cache
# ------------------------------------------------------------------------------
cache = SimpleCache()
