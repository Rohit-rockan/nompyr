# ==============================================================================
# SERVICES PACKAGE — Business Logic Layer
# ==============================================================================
# Purpose:
#     Houses all domain-specific business logic: metadata enrichment,
#     content filtering, recommendations, and external API integrations.
#     This layer has NO Flask dependency — it operates on plain Python
#     data structures.
#
# Need:
#     Separating business logic from HTTP handling (routes) enables:
#     1. Unit testing without spinning up a Flask server
#     2. Reusing logic across multiple routes
#     3. Future migration to async frameworks (Quart/FastAPI)
# ==============================================================================

from services.content_filter import (
    should_keep_hentai,
    filter_and_demote_hentai,
)

from services.anilist import (
    get_anilist_metadata,
    get_anilist_metadata_batch,
    enrich_results,
    clean_search_title,
)
from services.jikan import (
    map_jikan_to_nompyr,
    scrape_anime_info_jikan,
    fetch_episodes_jikan,
)
from services.enrichment import (
    enrich_detail_page,
    prefetch_home_metadata,
)
