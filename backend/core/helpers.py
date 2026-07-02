# ==============================================================================
# CORE — Shared Utility Helpers
# ==============================================================================
# Purpose:
#     Houses all generic, reusable utility functions used across multiple
#     layers (routes, services, scrapers). These are pure functions with
#     no Flask or database dependencies.
#
# Need:
#     Centralizes common logic (data normalization, safe execution,
#     list merging, date parsing, filter matching) so it is defined once
#     and imported everywhere, eliminating code duplication.
# ==============================================================================

import re
import time
from urllib.parse import urlparse

from config import Config


# ==============================================================================
# SECTION 1: DATA NORMALIZATION HELPERS
# ==============================================================================

def prefix_item(item, source):
    """
    Prefix an anime item's 'slug' and 'id' fields with its source provider name.

    Detailed Use:
        Ensures global uniqueness by prepending the provider name (e.g.,
        'animekai:one-piece') to slug and id fields. Prevents collisions
        when merging catalogs from multiple providers.

    Need:
        Without prefixing, two providers could return items with the same
        slug (e.g., 'one-piece'), causing the frontend to route to the
        wrong detail page.

    Args:
        item (dict): The anime metadata dictionary.
        source (str): The provider name (e.g., 'animekai', 'aniwatch').

    Returns:
        dict: A copy of the item with prefixed slug and id.
    """
    if not item:
        return item
    item = dict(item)
    slug = item.get("slug", "")
    if slug and not str(slug).startswith(f"{source}:"):
        item["slug"] = f"{source}:{slug}"

    item_id = item.get("id") or slug
    if item_id and not str(item_id).startswith(f"{source}:"):
        item["id"] = f"{source}:{item_id}"
    return item


def merge_lists(*lists):
    """
    Merge multiple lists using round-robin interleaving.

    Detailed Use:
        Takes N lists and produces a single merged list by alternating
        elements: first item from list 1, first from list 2, ..., then
        second item from list 1, second from list 2, etc.

    Need:
        Maintains provider variety on the homepage — prevents one fast
        provider's results from dominating the entire feed while slower
        providers' results are pushed to the bottom.

    Args:
        *lists: Variable number of lists to merge.

    Returns:
        list: A single merged list with round-robin element ordering.
    """
    merged = []
    max_len = max(len(lst) for lst in lists) if lists else 0
    for i in range(max_len):
        for lst in lists:
            if i < len(lst):
                merged.append(lst[i])
    return merged


def safe_run(func, *args, **kwargs):
    """
    Execute a function safely, returning an empty dict on any exception.

    Detailed Use:
        Wraps a function call in try-except, printing the error and
        returning {} if the function raises. Used to isolate individual
        scraper failures from the aggregated response.

    Need:
        Prevents the entire home feed or search response from failing
        when a single provider encounters scraper issues, network
        timeouts, or HTML structure changes.

    Args:
        func (callable): The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The function's return value, or {} on exception.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error executing {func.__name__}: {e}")
        return {}


# ==============================================================================
# SECTION 2: PARSING & VALIDATION HELPERS
# ==============================================================================

def parse_release_date_safe(date_str):
    """
    Parse a date string using multiple format patterns with regex fallback.

    Detailed Use:
        Attempts to parse the input using standard date formats
        ('%Y-%m-%d', '%b %d, %Y', etc.). If all formats fail, falls back
        to regex extraction of a 4-digit year.

    Need:
        Remote sources return dates in wildly inconsistent formats.
        This function normalizes them all into a comparable time.struct_time
        for sorting and filtering operations.

    Args:
        date_str (str): The raw date string to parse.

    Returns:
        time.struct_time or None: Parsed date, or None if unparseable.
    """
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y", "%B %d, %Y"):
        try:
            return time.strptime(date_str, fmt)
        except ValueError:
            pass
    match = re.search(r'\b(19\d\d|20\d\d)\b', date_str)
    if match:
        try:
            return time.strptime(match.group(1), "%Y")
        except ValueError:
            pass
    return None


def get_score_val(item):
    """
    Extract a float score from an anime item's rating fields.

    Detailed Use:
        Checks 'score', 'mal_score', and 'rating' fields (in that order)
        and converts the first non-empty value to a float.

    Need:
        Enables robust sorting by rating even when different providers
        store scores under different key names.

    Args:
        item (dict): The anime metadata dictionary.

    Returns:
        float: The numeric score, or 0.0 if unavailable.
    """
    val = item.get("score") or item.get("mal_score") or item.get("rating") or "N/A"
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def get_year_val(item):
    """
    Extract the release year as an integer from an anime item.

    Detailed Use:
        Scans the 'year', 'release', 'detail.released', and
        'detail.premiered' fields using regex to find a 4-digit year.

    Need:
        Enables calendar filtering and chronological sorting in the
        advanced library search.

    Args:
        item (dict): The anime metadata dictionary.

    Returns:
        int: The release year, or 0 if unavailable.
    """
    year_str = item.get("year") or ""
    try:
        match = re.search(r'\b(19\d\d|20\d\d)\b', str(year_str))
        if match:
            return int(match.group(1))
        date_str = (
            item.get("release")
            or item.get("detail", {}).get("released")
            or item.get("detail", {}).get("premiered")
            or ""
        )
        match = re.search(r'\b(19\d\d|20\d\d)\b', str(date_str))
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 0


# ==============================================================================
# SECTION 3: LIBRARY FILTERING HELPERS
# ==============================================================================

def matches_language(item, lang):
    """
    Check if an anime item matches a language availability filter.

    Detailed Use:
        Evaluates whether the item has sub, dub, or both language tracks
        by inspecting the 'language', 'sub_episodes', and 'dub_episodes'
        fields.

    Need:
        Powers the language filter in advanced search, letting users find
        specifically subbed or dubbed anime.

    Args:
        item (dict): The anime metadata dictionary.
        lang (str): The language filter ('sub', 'dub', 'both', or 'sub & dub').

    Returns:
        bool: True if the item matches the language constraint.
    """
    lang = lang.lower()
    languages = [l.lower() for l in (item.get("language") or [])]
    has_sub = (
        "sub" in languages
        or bool(item.get("sub_episodes"))
        or any("sub" in str(s).lower() for s in languages)
    )
    has_dub = (
        "dub" in languages
        or bool(item.get("dub_episodes"))
        or any("dub" in str(s).lower() for s in languages)
    )
    if lang == "sub":
        return has_sub
    elif lang == "dub":
        return has_dub
    elif lang in ("sub & dub", "both"):
        return has_sub and has_dub
    return True


def matches_genre(item, g):
    """
    Check if an anime item matches a genre filter.

    Detailed Use:
        Searches the item's genres list first, then falls back to
        checking the title, type, and slug fields for fuzzy matching.

    Need:
        Implements fuzzy genre search logic, capturing matches even when
        genre metadata is slightly inconsistent across providers.

    Args:
        item (dict): The anime metadata dictionary.
        g (str): The genre string to match (lowercase).

    Returns:
        bool: True if the item matches the genre constraint.
    """
    item_genres = [str(genre).lower() for genre in (item.get("genres") or [])]
    if any(g in genre for genre in item_genres):
        return True
    return (
        g in str(item.get("type", "")).lower()
        or g in str(item.get("title", "")).lower()
        or g in str(item.get("japanese_title", "")).lower()
        or g in str(item.get("slug", "")).lower()
    )


def matches_date_range(item, start_year, start_month, start_day,
                        end_year, end_month, end_day):
    """
    Check if an anime's release date falls within a date range.

    Detailed Use:
        Parses the item's release date and compares it against the
        specified start and end boundaries. Falls back to year-only
        comparison if full date parsing fails.

    Need:
        Powers the date-based filters in the advanced library search
        dashboard, allowing users to browse anime from specific eras.

    Args:
        item (dict): The anime metadata dictionary.
        start_year, start_month, start_day: Start of the date range.
        end_year, end_month, end_day: End of the date range.

    Returns:
        bool: True if the item falls within the date range.
    """
    date_str = (
        item.get("year")
        or item.get("release")
        or item.get("detail", {}).get("released")
        or item.get("detail", {}).get("premiered")
        or ""
    )
    item_t = parse_release_date_safe(date_str)
    if not item_t:
        try:
            year_val = int(item.get("year") or date_str[:4])
            if start_year and year_val < int(start_year):
                return False
            if end_year and year_val > int(end_year):
                return False
            return True
        except Exception:
            return True

    if start_year:
        try:
            st = time.struct_time((
                int(start_year), int(start_month or 1), int(start_day or 1),
                0, 0, 0, 0, 0, -1
            ))
            if item_t < st:
                return False
        except Exception:
            pass

    if end_year:
        try:
            et = time.struct_time((
                int(end_year), int(end_month or 12), int(end_day or 31),
                23, 59, 59, 0, 0, -1
            ))
            if item_t > et:
                return False
        except Exception:
            pass

    return True


# ==============================================================================
# SECTION 4: NETWORK & PROXY HELPERS
# ==============================================================================

def get_base_origin(url):
    """
    Extract the scheme + netloc (origin) from a URL.

    Detailed Use:
        Parses a URL and returns just the 'https://hostname/' portion,
        stripping path, query, and fragment components.

    Need:
        Used to construct clean Referer headers for proxy requests.
        Upstream servers often validate that the Referer matches their
        expected origin.

    Args:
        url (str): The full URL to extract the origin from.

    Returns:
        str: The origin URL (e.g., 'https://example.com/'), or ''.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass
    return ""


def get_proxy_session(url, headers):
    """
    Create a requests session with provider-specific cookie injection.

    Detailed Use:
        For anime.nexus and anime.delivery domains, injects Cloudflare
        bypass cookies and the correct User-Agent from the animenexus
        scraper module into the session.

    Need:
        Some providers use Cloudflare protection. Without the correct
        cookies and User-Agent, proxy requests return 403 Forbidden
        instead of the expected media content.

    Args:
        url (str): The URL being proxied.
        headers (dict): The request headers dict (modified in-place).

    Returns:
        requests.Session: A configured session for the proxy request.
    """
    import requests as _requests
    session = _requests.Session()
    if "anime.nexus" in url or "anime.delivery" in url:
        try:
            import scrapers.animenexus as animenexus
            headers["User-Agent"] = animenexus.CF_USER_AGENT
            if animenexus.CF_COOKIES:
                for c in animenexus.CF_COOKIES:
                    session.cookies.set(c["name"], c["value"], domain=c["domain"])
        except Exception as e:
            print(f"Error loading animenexus cookies for proxy: {e}")
    return session

def is_hentai(item):
    """
    Determine if an anime item is classified as hentai/adult content.
    """
    if not isinstance(item, dict):
        return False
    slug = str(item.get("slug", ""))
    item_id = str(item.get("id", ""))
    if slug.startswith("hanime:") or item_id.startswith("hanime:"):
        return True
    genres = [str(g).lower() for g in (item.get("genres") or [])]
    if "hentai" in genres:
        return True
    tags = [str(t).lower() for t in (item.get("tags") or [])]
    if "hentai" in tags:
        return True
    title = str(item.get("title", "")).lower()
    desc = str(item.get("description", "") or item.get("synopsis", "")).lower()
    if "hentai" in title or "hentai" in desc:
        return True
    return False

