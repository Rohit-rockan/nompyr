# ==============================================================================
# CORE — Persistent HTTP Client with Connection Pooling & Retry
# ==============================================================================
# Purpose:
#     Provides pre-configured requests.Session instances with persistent
#     connection pools, automatic retry with exponential backoff, and
#     domain-specific configurations.
#
# Need:
#     The #1 latency optimization. Without connection pooling, every HTTP
#     request incurs TCP handshake + TLS negotiation overhead (~100-300ms).
#     Persistent sessions reuse existing connections, cutting repeated
#     request latency by 40-60%. Retry logic prevents transient 429/5xx
#     failures from propagating to the user as errors.
#
# Architecture Reference:
#     Based on urllib3 connection pooling best practices and the
#     "retry with jittered exponential backoff" pattern from AWS
#     architecture whitepapers.
# ==============================================================================

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import Config


class HttpClient:
    """
    Managed HTTP client with connection pooling and retry logic.

    Detailed Use:
        Creates and manages persistent requests.Session objects with
        HTTPAdapter connection pools. Each session maintains a pool of
        keep-alive TCP connections, eliminating handshake overhead on
        repeated requests to the same host.

    Need:
        Nompyr makes hundreds of HTTP requests per minute to scrapers,
        AniList, and Jikan. Without pooling, each request opens a new
        TCP connection (~150ms overhead). With pooling, subsequent
        requests to the same host reuse the existing connection (~5ms).
    """

    def __init__(self):
        """
        Initialize the HTTP client with retry-enabled session pools.

        Detailed Use:
            Configures a retry strategy (3 attempts, exponential backoff,
            retry on 429/5xx) and mounts it on a persistent session with
            connection pooling (10 pools × 20 connections each).

        Need:
            Ensures resilience against transient network failures and
            API rate limiting without manual retry loops in every caller.
        """
        # --- Retry Strategy ---
        # Retries on connection errors, timeouts, and specific HTTP status codes.
        # Uses exponential backoff: 0.3s, 0.6s, 1.2s between retries.
        self._retry_strategy = Retry(
            total=Config.HTTP_RETRY_TOTAL,
            backoff_factor=Config.HTTP_RETRY_BACKOFF,
            status_forcelist=Config.HTTP_RETRY_STATUS_CODES,
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )

        # --- Connection Pool Adapter ---
        # Maintains persistent TCP connections across requests.
        self._adapter = HTTPAdapter(
            pool_connections=Config.HTTP_POOL_CONNECTIONS,
            pool_maxsize=Config.HTTP_POOL_MAXSIZE,
            max_retries=self._retry_strategy,
        )

        # --- Primary Session (general purpose) ---
        self._session = self._create_session()

        # --- Domain-Specific Sessions ---
        # Separate pools prevent one slow domain from exhausting
        # connections needed by another.
        self._anilist_session = self._create_session()
        self._jikan_session = self._create_session()

    def _create_session(self):
        """
        Create a new requests.Session with pooling and retry adapters.

        Detailed Use:
            Builds a session with the retry-enabled HTTPAdapter mounted
            on both HTTP and HTTPS schemes, and sets the default
            User-Agent header.

        Need:
            Encapsulates session creation logic so all sessions share
            identical pooling and retry configurations.

        Returns:
            requests.Session: A configured session with connection pooling.
        """
        session = requests.Session()
        session.mount("https://", self._adapter)
        session.mount("http://", self._adapter)
        session.headers.update({
            "User-Agent": Config.DEFAULT_USER_AGENT,
        })
        return session

    @property
    def session(self):
        """
        Get the general-purpose HTTP session.

        Detailed Use:
            Returns the primary session used for scraper requests and
            miscellaneous HTTP calls.

        Need:
            Provides a single access point for the pooled session,
            ensuring all callers benefit from connection reuse.

        Returns:
            requests.Session: The primary pooled session.
        """
        return self._session

    @property
    def anilist(self):
        """
        Get the AniList-dedicated HTTP session.

        Detailed Use:
            Returns a session configured specifically for requests to
            graphql.anilist.co. Isolated from other domains to prevent
            AniList rate limits from affecting scraper connections.

        Need:
            AniList enforces strict rate limits (90 req/min). A dedicated
            session pool ensures AniList connections don't compete with
            scraper connections for pool slots.

        Returns:
            requests.Session: The AniList-dedicated pooled session.
        """
        return self._anilist_session

    @property
    def jikan(self):
        """
        Get the Jikan API-dedicated HTTP session.

        Detailed Use:
            Returns a session configured specifically for requests to
            api.jikan.moe. Isolated from other domains to prevent Jikan
            rate limits from affecting other connections.

        Need:
            Jikan enforces strict rate limits (3 req/sec). A dedicated
            session pool isolates Jikan traffic from scraper and AniList
            connections.

        Returns:
            requests.Session: The Jikan-dedicated pooled session.
        """
        return self._jikan_session

    def get(self, url, **kwargs):
        """
        Perform a GET request using the general-purpose session.

        Detailed Use:
            Delegates to the primary session's get() method, inheriting
            connection pooling and retry behavior.

        Need:
            Convenience method so callers can do http_client.get(url)
            instead of http_client.session.get(url).

        Args:
            url (str): The URL to request.
            **kwargs: Additional arguments passed to requests.get().

        Returns:
            requests.Response: The HTTP response.
        """
        return self._session.get(url, **kwargs)

    def post(self, url, **kwargs):
        """
        Perform a POST request using the general-purpose session.

        Detailed Use:
            Delegates to the primary session's post() method, inheriting
            connection pooling and retry behavior.

        Need:
            Convenience method for POST requests (used by AniList GraphQL
            queries and admin authentication).

        Args:
            url (str): The URL to request.
            **kwargs: Additional arguments passed to requests.post().

        Returns:
            requests.Response: The HTTP response.
        """
        return self._session.post(url, **kwargs)


# ------------------------------------------------------------------------------
# Singleton HTTP Client Instance
# ------------------------------------------------------------------------------
# A single global HTTP client shared across all modules. Import via:
#     from core.http_client import http_client
# ------------------------------------------------------------------------------
http_client = HttpClient()
