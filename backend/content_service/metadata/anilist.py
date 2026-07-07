# ==============================================================================
# SERVICES — AniList GraphQL Metadata Integration
# ==============================================================================
# Purpose:
#     Handles all interactions with the AniList GraphQL API: single-title
#     metadata lookups, batch resolution for homepage feeds, and result
#     enrichment (poster + score replacement).
#
# Need:
#     Scraped anime data often lacks high-quality posters, accurate scores,
#     trailer URLs, studio info, and airing schedules. AniList provides
#     all of these via a single GraphQL query, transforming raw scraper
#     output into rich, polished detail pages.
# ==============================================================================

import re
import time
import datetime

from config import Config
from core.cache import cache
from core.http_client import http_client
from core.helpers import is_hentai


# ==============================================================================
# SECTION 1: TITLE CLEANING & VARIANT GENERATION
# ==============================================================================

def clean_search_title(title):
    """
    Clean a raw anime title and generate search variants for API matching.

    Detailed Use:
        Strips common suffixes (e.g., '(Dub)', '[1080p]', '[Uncensored]'),
        removes punctuation and brackets, and generates multiple search
        variants: clean title, without season markers, split by separators,
        and truncated prefixes.

    Need:
        AniList's search requires clean, exact title fragments to yield
        reliable results. Raw scraper titles contain noise like '(Sub)',
        '[Uncensored]', season markers, and quality tags that must be
        removed before querying.

    Args:
        title (str): The raw anime title from a scraper.

    Returns:
        list[str]: Deduplicated list of search title variants, ordered
                   from most specific to most general.
    """
    if not title:
        return []

    extra_variants = []
    if "..." in title:
        parts = title.split("...")
        first_part = parts[0].strip()
        words_first = first_part.split()
        if len(words_first) > 1:
            clean_prefix = " ".join(words_first[:-1])
            clean_prefix = re.sub(r'[^a-zA-Z0-9\s]+$', '', clean_prefix).strip()
            if clean_prefix:
                extra_variants.append(clean_prefix)
        elif words_first:
            clean_prefix = re.sub(r'[^a-zA-Z0-9\s]+$', '', words_first[0]).strip()
            if clean_prefix:
                extra_variants.append(clean_prefix)

    # Remove common tags in brackets/parentheses
    tag_pattern = (
        r'[\(\[\{](?:dub|sub|uncensored|uncut|batch|multi-sub|split cour|'
        r'1080p|720p|h264|hevc|x264|x265|bluray|bd|web-dl|web|dvd|tv|'
        r'movie|ova|ona|special)[\)\]\}]'
    )
    title_cleaned = re.sub(tag_pattern, '', title, flags=re.IGNORECASE)

    # Strip quotes
    title_cleaned = title_cleaned.replace('"', '').replace("'", "")

    # Remove bracket symbols but keep contents
    for ch in ['[', ']', '(', ')', '{', '}', '【', '】']:
        title_cleaned = title_cleaned.replace(ch, '')

    # Replace ellipsis with space
    title_cleaned = re.sub(r'\.\.\.+', ' ', title_cleaned)

    # Normalize spaces
    title_cleaned = re.sub(r'\s+', ' ', title_cleaned).strip()

    variants = []

    # Add extra variants first (from ellipsis processing)
    for ev in extra_variants:
        if ev.lower() not in [v.lower() for v in variants]:
            variants.append(ev)

    # Variant 1: Cleaned title
    if title_cleaned:
        variants.append(title_cleaned)

    # Variant 2: Without season/part suffixes
    no_season = re.sub(
        r'\b\d+(st|nd|rd|th)?\s+season\b', '', title_cleaned,
        flags=re.IGNORECASE
    )
    no_season = re.sub(
        r'\bseason\s+\d+\b', '', no_season, flags=re.IGNORECASE
    )
    no_season = re.sub(
        r'\bpart\s+\d+\b', '', no_season, flags=re.IGNORECASE
    )
    no_season = re.sub(
        r'\bpart\s+[i|v|x]+\b', '', no_season, flags=re.IGNORECASE
    )
    no_season = re.sub(r'\s+', ' ', no_season).strip()
    if no_season and no_season.lower() != title_cleaned.lower():
        variants.append(no_season)

    # Variant 3: Split by common separators
    for separator in (':', '-', '–', '—', ','):
        if separator in title_cleaned:
            parts = title_cleaned.split(separator)
            first_part = parts[0].strip()
            if first_part and len(first_part.split()) >= 2:
                variants.append(first_part)

    # Variant 4: Truncated to first N words
    words = title_cleaned.split()
    if len(words) > 6:
        variants.append(" ".join(words[:6]))
    if len(words) > 4:
        variants.append(" ".join(words[:4]))
    if len(words) > 2:
        variants.append(" ".join(words[:2]))

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for v in variants:
        if v and v.lower() not in seen:
            seen.add(v.lower())
            deduped.append(v)

    return deduped


# ==============================================================================
# SECTION 2: SINGLE TITLE METADATA QUERY
# ==============================================================================

def _build_default_metadata():
    """
    Build a default metadata dict for when AniList returns no results.

    Returns:
        dict: Default metadata with empty/placeholder values.
    """
    return {
        "poster": "",
        "score": "N/A",
        "trailer_url": "",
        "type": "TV",
        "status": "Unknown",
        "episodes": None,
        "year": "TBA",
        "genres": [],
        "studio": "Unknown Studio",
        "schedule": "TBA",
    }


def get_anilist_metadata(title):
    """
    Fetch detailed metadata for an anime from AniList's GraphQL API.

    Detailed Use:
        Generates title search variants, builds a multi-alias GraphQL
        query, and dispatches it to AniList. Parses the response to
        extract poster image, score, trailer URL, format, status,
        studio, genres, year, and airing schedule.

    Need:
        Enriches raw scraper data with high-quality metadata that
        scrapers often miss: official poster art, MAL/AniList scores,
        YouTube trailer links, studio names, and next-episode schedules.

    Args:
        title (str): The anime title to look up.

    Returns:
        dict: Metadata dict with keys: poster, score, trailer_url,
              type, status, episodes, year, genres, studio, schedule.
    """
    if not title:
        return _build_default_metadata()

    cache_key = f"metadata:{title.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    variants = clean_search_title(title)
    if not variants:
        res = _build_default_metadata()
        cache.set(cache_key, res, timeout=Config.CACHE_TTL_METADATA_MISS)
        return res

    # Limit to max variants to conserve query complexity
    variants = variants[:Config.ANILIST_MAX_VARIANTS]

    # Build dynamic GraphQL query with aliases for each variant
    query_args = ", ".join(f"$s{i}: String" for i in range(len(variants)))
    query_body = ""
    for i in range(len(variants)):
        query_body += f"""
        q{i}: Page(page: 1, perPage: 1) {{
            media(search: $s{i}, type: ANIME) {{
                id
                coverImage {{
                    extraLarge
                    large
                }}
                bannerImage
                averageScore
                format
                status
                episodes
                seasonYear
                genres
                studios(isMain: true) {{
                    nodes {{
                        name
                    }}
                }}
                nextAiringEpisode {{
                    airingAt
                    episode
                }}
                trailer {{
                    id
                    site
                }}
            }}
        }}
        """

    query = f"query ({query_args}) {{ {query_body} }}"
    variables = {f"s{i}": variants[i] for i in range(len(variants))}

    try:
        r = http_client.anilist.post(
            Config.ANILIST_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers={"User-Agent": Config.DEFAULT_USER_AGENT},
            timeout=Config.ANILIST_TIMEOUT,
        )
        if r.status_code == 429:
            print(f"Rate limited by AniList (429) for '{title}'.")
            return _build_default_metadata()

        if r.status_code == 200:
            data = r.json().get("data", {})
            for i in range(len(variants)):
                media_list = data.get(f"q{i}", {}).get("media", [])
                if media_list and media_list[0]:
                    media = media_list[0]
                    cover = (
                        media.get("coverImage", {}).get("extraLarge")
                        or media.get("coverImage", {}).get("large")
                        or ""
                    )
                    banner = media.get("bannerImage") or cover
                    score = media.get("averageScore")
                    score_str = f"{score/10:.1f}" if score is not None else "N/A"

                    # Trailer
                    trailer_data = media.get("trailer")
                    trailer_url = ""
                    if trailer_data and trailer_data.get("site") == "youtube":
                        t_id = trailer_data.get("id")
                        if t_id:
                            trailer_url = f"https://www.youtube.com/embed/{t_id}"

                    # Format mapping
                    format_val = media.get("format")
                    format_map = {
                        "TV": "TV", "TV_SHORT": "TV Short", "MOVIE": "Movie",
                        "SPECIAL": "Special", "OVA": "OVA", "ONA": "ONA",
                        "MUSIC": "Music",
                    }
                    type_val = format_map.get(format_val, format_val) if format_val else "TV"

                    # Status mapping
                    status_raw = media.get("status")
                    status_map = {
                        "FINISHED": "Completed", "RELEASING": "Ongoing",
                        "NOT_YET_RELEASED": "Upcoming", "HIATUS": "Hiatus",
                        "CANCELLED": "Cancelled",
                    }
                    status_val = status_map.get(status_raw, status_raw) if status_raw else "Unknown"

                    episodes_val = media.get("episodes")
                    year_val = media.get("seasonYear") or "TBA"
                    genres_val = media.get("genres") or []

                    studios_nodes = media.get("studios", {}).get("nodes", [])
                    studio_val = (
                        studios_nodes[0].get("name")
                        if studios_nodes
                        else "Unknown Studio"
                    )

                    # Airing schedule
                    schedule_val = "TBA"
                    next_ep = media.get("nextAiringEpisode")
                    if next_ep:
                        ep_num = next_ep.get("episode")
                        airing_at = next_ep.get("airingAt")
                        try:
                            dt = datetime.datetime.fromtimestamp(
                                airing_at, tz=datetime.timezone.utc
                            )
                            day_name = dt.strftime("%A")
                            time_str = dt.strftime("%I:%M %p UTC")
                            schedule_val = f"Ep {ep_num}: {day_name} {time_str}"
                        except Exception:
                            schedule_val = f"Ep {ep_num} upcoming"

                    res = {
                        "poster": cover,
                        "banner": banner,
                        "score": score_str,
                        "trailer_url": trailer_url,
                        "type": type_val,
                        "status": status_val,
                        "episodes": episodes_val,
                        "year": year_val,
                        "genres": genres_val,
                        "studio": studio_val,
                        "schedule": schedule_val,
                    }
                    cache.set(cache_key, res, timeout=Config.CACHE_TTL_METADATA_HIT)
                    return res
    except Exception as e:
        print(f"Error fetching AniList metadata for {title}: {e}")

    res = _build_default_metadata()
    cache.set(cache_key, res, timeout=Config.CACHE_TTL_METADATA_MISS)
    return res


# ==============================================================================
# SECTION 3: BATCH METADATA RESOLUTION
# ==============================================================================

def _fetch_single_batch(batch, batch_idx):
    """
    Execute a single batched GraphQL query for multiple anime titles.

    Detailed Use:
        Builds a combined GraphQL query with aliases for each title's
        variants, dispatches it as one HTTP request, and maps results
        back to their original titles.

    Need:
        Saves network roundtrips and mitigates rate limits when
        processing large feeds. A single batch query replaces 10+
        individual queries.

    Args:
        batch (list[str]): List of anime titles to look up.
        batch_idx (int): Batch index (for logging).

    Returns:
        dict: Mapping of title -> {poster, score} for resolved titles.
    """
    query_variables = {}
    query_args_list = []
    query_body_parts = []
    valid_batch_indices = []

    for idx, title_item in enumerate(batch):
        variants = clean_search_title(title_item)
        if not variants:
            continue

        variants = variants[:Config.ANILIST_BATCH_MAX_VARIANTS]
        valid_batch_indices.append((idx, title_item, variants))

        for v_idx, variant in enumerate(variants):
            var_name = f"b{idx}_v{v_idx}"
            query_args_list.append(f"${var_name}: String")
            query_variables[var_name] = variant

            alias_name = f"alias_{idx}_{v_idx}"
            query_body_parts.append(f"""
            {alias_name}: Page(page: 1, perPage: 1) {{
                media(search: ${var_name}, type: ANIME) {{
                    coverImage {{
                        extraLarge
                        large
                    }}
                    bannerImage
                    averageScore
                }}
            }}
            """)

    if not query_body_parts:
        return {}

    query_args_str = ", ".join(query_args_list)
    query_body_str = "\n".join(query_body_parts)
    query = f"query ({query_args_str}) {{ {query_body_str} }}"

    batch_results = {}
    try:
        r = http_client.anilist.post(
            Config.ANILIST_GRAPHQL_URL,
            json={"query": query, "variables": query_variables},
            headers={"User-Agent": Config.DEFAULT_USER_AGENT},
            timeout=Config.ANILIST_BATCH_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json().get("data", {}) or {}
            for idx, title_item, variants in valid_batch_indices:
                resolved_meta = None
                for v_idx in range(len(variants)):
                    alias_name = f"alias_{idx}_{v_idx}"
                    media_list = data.get(alias_name, {}).get("media", [])
                    if media_list and media_list[0]:
                        media = media_list[0]
                        cover = (
                            media.get("coverImage", {}).get("extraLarge")
                            or media.get("coverImage", {}).get("large")
                            or ""
                        )
                        banner = media.get("bannerImage") or cover
                        score = media.get("averageScore")
                        score_str = f"{score/10:.1f}" if score is not None else "N/A"
                        resolved_meta = {"poster": cover, "banner": banner, "score": score_str}
                        break
                if resolved_meta:
                    batch_results[title_item] = resolved_meta
                else:
                    batch_results[title_item] = {"poster": "", "score": "N/A"}
        else:
            print(
                f"GraphQL batch request failed with status code "
                f"{r.status_code}: {r.text}"
            )
    except Exception as e:
        print(f"Error executing batch query: {e}")

    return batch_results


def get_anilist_metadata_batch(titles):
    """
    Resolve metadata for multiple titles with cache-first batch queries.

    Detailed Use:
        Checks cache for each title first. Uncached titles are grouped
        into batches of ANILIST_BATCH_SIZE and resolved sequentially
        with rate-limit-respecting delays between batches.

    Need:
        Minimizes AniList rate-limiting penalties while ensuring fast
        metadata resolution for homepage feeds that contain 50+ items.

    Args:
        titles (list[str]): List of anime titles to resolve.

    Returns:
        dict: Mapping of title -> {poster, score} for all input titles.
    """
    if not titles:
        return {}

    results = {}
    uncached_titles = []

    # 1. Check cache first
    for title in titles:
        if not title:
            continue
        cache_key = f"metadata:{title.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            results[title] = cached
        else:
            if title not in uncached_titles:
                uncached_titles.append(title)

    if not uncached_titles:
        return results

    # 2. Query uncached titles in batches
    batch_size = Config.ANILIST_BATCH_SIZE
    batches = [
        uncached_titles[i:i + batch_size]
        for i in range(0, len(uncached_titles), batch_size)
    ]
    batches = batches[:Config.ANILIST_MAX_BATCHES]

    for idx, batch in enumerate(batches):
        if idx > 0:
            time.sleep(Config.ANILIST_BATCH_DELAY)
        try:
            batch_res = _fetch_single_batch(batch, idx)
            if batch_res:
                for title, meta in batch_res.items():
                    results[title] = meta
                    cache_key = f"metadata:{title.lower()}"
                    ttl = (
                        Config.CACHE_TTL_METADATA_HIT
                        if meta.get("poster")
                        else Config.CACHE_TTL_METADATA_MISS
                    )
                    cache.set(cache_key, meta, timeout=ttl)
            else:
                break  # Possibly rate-limited, stop early
        except Exception as e:
            print(f"Error in batch resolution: {e}")

    # Fill remaining uncached entries with defaults
    for title in uncached_titles:
        if title not in results:
            results[title] = {"poster": "", "banner": "", "score": "N/A"}

    return results


# ==============================================================================
# SECTION 4: RESULT ENRICHMENT PIPELINE
# ==============================================================================

def enrich_results(results):
    """
    Enrich a list of anime items with AniList metadata.

    Detailed Use:
        Scans a result list for items with missing or broken posters
        and scores. Identifies titles needing enrichment, resolves
        metadata in batch, and updates items in-place with high-quality
        poster URLs and accurate scores.

    Need:
        Maintains high visual polish across homepage cards by replacing
        broken image URLs, missing scores, and hanime CDN posters with
        clean AniList artwork.

    Args:
        results (list[dict]): List of anime metadata dictionaries.

    Returns:
        list[dict]: The input list with enriched poster/score fields.
    """
    if not results:
        return results

    to_enrich_indices = []
    titles_to_enrich = []

    for idx, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        poster = item.get("poster", "")
        score = item.get("score") or item.get("mal_score") or "N/A"
        slug = item.get("slug", "")

        is_hanime = False
        if slug and str(slug).startswith("hanime:"):
            is_hanime = True
        if poster and (
            "hanime-cdn.com" in poster
            or "hanime.tv" in poster
            or "htv-services.com" in poster
        ):
            is_hanime = True

        needs_enrich = False
        if score == "N/A" or not score:
            needs_enrich = True
        if not poster or "animeverse.to/i/" in poster or "nekkoto" in poster:
            needs_enrich = True
        if is_hanime:
            needs_enrich = True

        if needs_enrich:
            title = item.get("title", "")
            if title:
                to_enrich_indices.append(idx)
                titles_to_enrich.append(title)

    if not titles_to_enrich:
        return results

    # Batch resolve metadata
    enriched_data = get_anilist_metadata_batch(titles_to_enrich)

    for idx, title in zip(to_enrich_indices, titles_to_enrich):
        meta = enriched_data.get(title)
        if meta:
            orig_poster = results[idx].get("poster", "")
            is_orig_hanime = False
            if orig_poster and (
                "hanime-cdn.com" in orig_poster
                or "hanime.tv" in orig_poster
                or "htv-services.com" in orig_poster
            ):
                is_orig_hanime = True

            if meta.get("poster") and (
                not orig_poster
                or "animeverse.to/i/" in orig_poster
                or "nekkoto" in orig_poster
                or is_orig_hanime
            ):
                results[idx]["poster"] = meta["poster"]
                results[idx]["banner"] = meta.get("banner") or meta["poster"]
            if meta.get("score") and meta["score"] != "N/A":
                results[idx]["score"] = meta["score"]
                results[idx]["mal_score"] = meta["score"]

    return results
