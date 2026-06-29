# ==============================================================================
# SERVICES — Content Filtering (Hentai Detection & Demotion)
# ==============================================================================
# Purpose:
#     Manages content filtering policies for the homepage and search feeds.
#     Detects hentai content and applies probabilistic filtering and
#     demotion (pushing adult items to the end of lists).
#
# Need:
#     Maintains a clean, family-friendly default homepage while allowing
#     a controlled small sample of adult content. Prevents overwhelming
#     mainstream discovery channels with NSFW material.
# ==============================================================================

from services.recommender import is_hentai
from config import Config


def should_keep_hentai(item):
    """
    Determine if a hentai item passes the probabilistic keep filter.

    Detailed Use:
        First checks if the item is flagged as hentai. If so, calculates
        a deterministic hash of the title and uses modular arithmetic to
        decide whether to keep it (~14.3% probability with mod 7).

    Need:
        Provides a deterministic, title-based sampling mechanism so the
        same title always produces the same keep/reject decision (no
        randomness between page loads).

    Args:
        item (dict): The anime metadata dictionary.

    Returns:
        bool: True if the item should be kept (either not hentai, or
              passed the probability filter).
    """
    if not is_hentai(item):
        return True
    title = item.get("title", "")
    h = sum(ord(c) for c in title) if title else 0
    return h % Config.HENTAI_KEEP_PROBABILITY_MOD == 0


def filter_and_demote_hentai(items, max_hentai=None):
    """
    Filter a list to limit hentai items and push them to the end.

    Detailed Use:
        Separates items into non-hentai and hentai groups. Applies the
        probabilistic keep filter to hentai items, caps the count to
        max_hentai, and appends them after all non-hentai items.

    Need:
        Ensures the homepage visual presentation remains balanced and
        clean across all providers, while still including a small
        curated sample of adult content.

    Args:
        items (list): List of anime metadata dictionaries.
        max_hentai (int, optional): Maximum hentai items to keep.
            Defaults to Config.MAX_HENTAI_DEFAULT (2).

    Returns:
        list: Filtered and reordered list with hentai items demoted.
    """
    if max_hentai is None:
        max_hentai = Config.MAX_HENTAI_DEFAULT
    if not items:
        return items
    non_hentai = []
    hentai = []
    for item in items:
        if is_hentai(item):
            if should_keep_hentai(item):
                hentai.append(item)
        else:
            non_hentai.append(item)
    hentai = hentai[:max_hentai]
    return non_hentai + hentai
