# ==============================================================================
# NOMPYR BACKEND — Application Factory
# ==============================================================================
# Purpose:
#     Slim application factory that creates and configures the Flask app,
#     initializes the database, and registers all route blueprints.
#     Replaces the original 2246-line monolithic app.py.
#
# Architecture:
#     backend/
#     ├── app.py              ← This file (slim factory)
#     ├── config.py           ← Centralized settings
#     ├── core/               ← Cache, database, HTTP client, helpers
#     ├── services/           ← Business logic (AniList, Jikan, enrichment)
#     ├── routes/             ← Flask Blueprints (HTTP layer)
#     └── scrapers/           ← Provider-specific scrapers (unchanged)
# ==============================================================================

from flask import Flask
from flask_cors import CORS

from config import Config
from core.database import init_db
from routes import register_blueprints


def create_app():
    """
    Application factory for the Nompyr Flask backend.

    Detailed Use:
        Creates a Flask application instance, enables CORS, initializes
        the SQLite database, and registers all route blueprints.

    Need:
        Factory pattern enables clean testing, Vercel deployment, and
        future migration to async frameworks. The app instance is also
        exported at module level for backward compatibility with
        api/index.py and direct execution.

    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__)
    CORS(app, origins=Config.CORS_ORIGINS)
    init_db()
    register_blueprints(app)
    return app


# Module-level app instance for backward compatibility:
#   - api/index.py does `from app import app`
#   - Direct execution with `python app.py`
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
