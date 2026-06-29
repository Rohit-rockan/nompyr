# ==============================================================================
# CORE PACKAGE — Shared Infrastructure Layer
# ==============================================================================
# Purpose:
#     Exposes the foundational infrastructure components used by all other layers:
#     cache, database, HTTP client pool, and utility helpers.
#
# Need:
#     Provides a clean import surface so routes and services can do:
#         from core import cache, get_db, http_client
#     instead of importing from individual submodules.
# ==============================================================================

from core.cache import cache
from core.database import init_db, get_db
from core.http_client import http_client
from core.helpers import (
    safe_run,
    prefix_item,
    merge_lists,
    parse_release_date_safe,
    get_score_val,
    get_year_val,
    matches_language,
    matches_genre,
    matches_date_range,
    get_base_origin,
    get_proxy_session,
)
