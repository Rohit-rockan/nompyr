# ==============================================================================
# ROUTES PACKAGE — Blueprint Registration
# ==============================================================================
# Purpose:
#     Central registry for all Flask Blueprints. The app factory calls
#     register_blueprints(app) once during startup to mount all route
#     modules onto the application.
#
# Need:
#     Decouples route definition from app creation, enabling each route
#     module to be developed and tested independently. Adding a new
#     API domain requires only creating a new file and adding one line
#     to this registry.
# ==============================================================================


def register_blueprints(app):
    """
    Register all Flask Blueprints with the application.

    Detailed Use:
        Imports each route module's Blueprint and registers it with the
        Flask app. Blueprints are registered in dependency order: core
        utilities first, then domain-specific routes.

    Need:
        Provides a single function for the app factory to call, keeping
        app.py clean and eliminating circular import issues by deferring
        all route imports to registration time.

    Args:
        app (Flask): The Flask application instance.
    """
    from core_website.home import home_bp
    from content_service.search.api import search_bp
    from content_service.episodes.api import anime_bp
    from streaming_service.server_selection.api import source_bp
    from streaming_service.playlist_handling.api import proxy_bp
    from content_service.genres.api import jikan_bp
    from admin_dashboard.api import admin_bp
    from content_service.metadata.reviews import reviews_bp
    from content_service.genres.recommendations import recommendations_bp
    from core_website.continue_watching.api import history_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(anime_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(jikan_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(history_bp)
