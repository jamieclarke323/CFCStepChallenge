"""Flask application factory."""
import os
from datetime import timedelta

from flask import Flask

from .config import Config
from .extensions import db, login_manager, csrf, migrate, limiter


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "info"
    login_manager.remember_cookie_duration = timedelta(days=app.config["REMEMBER_COOKIE_DAYS"])
    login_manager.session_protection = "strong"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Make the session permanent (and thus subject to PERMANENT_SESSION_LIFETIME)
    # on every request so "remember me" style persistence works even without
    # the remember cookie, satisfying the 35-day login requirement.
    @app.before_request
    def _make_session_permanent():
        from flask import session
        session.permanent = True

    from .auth.routes import auth_bp
    from .steps.routes import steps_bp
    from .progress.routes import progress_bp
    from .team.routes import team_bp
    from .leaderboard.routes import leaderboard_bp
    from .messages.routes import messages_bp
    from .main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(steps_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(messages_bp)

    from . import errors
    from . import template_filters

    errors.register_error_handlers(app)
    template_filters.register_template_filters(app)

    @app.after_request
    def _set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; base-uri 'self'; form-action 'self'",
        )
        return response

    return app
