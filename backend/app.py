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

from flask import Flask, jsonify
from flask_cors import CORS

from flask_apscheduler import APScheduler

from config import Config
from core.database import init_db
from registry import register_blueprints
from shared.logger import logger
from shared.discord_notifier import mechanic_alert

scheduler = APScheduler()


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
    
    # Initialize APScheduler for The Librarian Bot
    scheduler.init_app(app)
    scheduler.start()
    
    # Register the Librarian Database Cleanup Task
    # Runs every 24 hours
    from background_workers.librarian import run_librarian_cleanup
    scheduler.add_job(
        id='librarian_db_cleanup',
        func=run_librarian_cleanup,
        trigger='interval',
        hours=24
    )
    
    # Register The Mayor Analytics Report
    # Runs every 24 hours
    from background_workers.mayor import run_mayor_tasks
    scheduler.add_job(
        id='mayor_analytics_report',
        func=run_mayor_tasks,
        trigger='interval',
        hours=24
    )
    
    # Register The Guard Security Scan
    # Runs every 10 minutes
    from background_workers.guard import run_guard_tasks
    scheduler.add_job(
        id='guard_security_scan',
        func=run_guard_tasks,
        trigger='interval',
        minutes=10
    )
    
    # Register The Tester QA Checks
    # Runs every 30 minutes
    from background_workers.tester import run_tester_tasks
    scheduler.add_job(
        id='tester_qa_checks',
        func=run_tester_tasks,
        trigger='interval',
        minutes=30
    )
    
    # Register The Manager Infrastructure Checks
    # Runs every hour
    from background_workers.manager import run_manager_tasks
    scheduler.add_job(
        id='manager_infra_checks',
        func=run_manager_tasks,
        trigger='interval',
        hours=1
    )
    
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        
        # The Mechanic Bot sends an alert to Discord
        mechanic_alert(
            content=f"🚨 **Unhandled Exception Detected!**\n`{str(e)}`",
            embeds=[{
                "title": "Stack Trace",
                "description": f"```python\n{str(e)}\n```",
                "color": 16711680 # Red
            }]
        )
        
        return jsonify({
            "success": False,
            "error": "Internal Server Error",
            "message": str(e) if app.debug else "An unexpected error occurred."
        }), 500

    return app


# Module-level app instance for backward compatibility:
#   - api/index.py does `from app import app`
#   - Direct execution with `python app.py`
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
